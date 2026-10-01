"""Formatting pipeline regression tests.

Run with: python3 tests/test_telegram_format.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.telegram_format import (
    prepare_content_for_telegram,
    build_post_content,
    clamp_telegram_text,
    split_telegram_text,
    normalize_newlines,
    html_to_preview_html,
    visible_length,
    TELEGRAM_TEXT_LIMIT,
    TELEGRAM_CAPTION_LIMIT,
    _TAG_RE,
    _canonical_tag,
)


def assert_valid_telegram_html(case, html, limit=TELEGRAM_TEXT_LIMIT):
    """Assert html only uses Telegram tags, is balanced, and fits the limit."""
    case.assertNotIn('\r', html, 'carriage return present')
    case.assertNotIn('<br', html.lower(), '<br> is not a Telegram tag')
    case.assertLessEqual(len(html), limit, f'{len(html)} chars exceeds {limit}')

    stack = []
    for match in _TAG_RE.finditer(html):
        closing, raw_tag, _, _ = match.groups()
        canonical = _canonical_tag(raw_tag)
        case.assertIsNotNone(canonical, f'unsupported tag {match.group(0)!r}')
        if closing:
            case.assertIn(canonical, stack, f'stray closing tag {match.group(0)!r}')
            stack.remove(canonical)
        else:
            stack.append(canonical)
    case.assertEqual(stack, [], f'unclosed tags: {stack}')


class TestLineBreaks(unittest.TestCase):
    def test_newline_conventions_collapse_to_lf(self):
        for source in ('a\r\nb', 'a\rb', 'a\nb', 'a\u2028b', 'a\u000bb'):
            self.assertEqual(normalize_newlines(source), 'a\nb', repr(source))

    def test_single_newlines_are_preserved(self):
        self.assertEqual(
            prepare_content_for_telegram('uno\ndos\ntres'),
            'uno\ndos\ntres',
        )

    def test_blank_lines_are_preserved(self):
        self.assertEqual(
            prepare_content_for_telegram('uno\n\ndos'),
            'uno\n\ndos',
        )

    def test_output_never_contains_br(self):
        html = prepare_content_for_telegram('a\nb\n\nc')
        self.assertNotIn('<br', html.lower())

    def test_preview_html_converts_newlines_to_br(self):
        self.assertEqual(html_to_preview_html('a\nb'), 'a<br/>b')
        self.assertEqual(html_to_preview_html('a\n\nb'), 'a<br/><br/>b')


class TestEscaping(unittest.TestCase):
    def test_html_specials_are_escaped(self):
        html = prepare_content_for_telegram('5 < 10 & 20 > 3')
        self.assertEqual(html, '5 &lt; 10 &amp; 20 &gt; 3')
        assert_valid_telegram_html(self, html)

    def test_angle_brackets_do_not_create_tags(self):
        html = prepare_content_for_telegram('<3 amor')
        self.assertEqual(html, '&lt;3 amor')
        assert_valid_telegram_html(self, html)

    def test_unsupported_html_is_escaped_and_text_preserved(self):
        html = prepare_content_for_telegram('<h1>titulo</h1>')
        assert_valid_telegram_html(self, html)
        self.assertEqual(html, '&lt;h1&gt;titulo&lt;/h1&gt;')

    def test_angle_brackets_around_a_word_are_not_swallowed(self):
        html = prepare_content_for_telegram('Hola <mundo>')
        assert_valid_telegram_html(self, html)
        self.assertEqual(html, 'Hola &lt;mundo&gt;')

    def test_javascript_href_is_never_a_live_link(self):
        html = prepare_content_for_telegram('<a href="javascript:alert(1)">x</a>')
        assert_valid_telegram_html(self, html)
        self.assertNotIn('<a', html)
        # Shown as literal text instead: no injection, no lost content.
        self.assertIn('javascript:', html)
        self.assertIn('x', html)

    def test_unsafe_scheme_keeps_opener_and_closer_symmetric(self):
        html = prepare_content_for_telegram('<a href="ftp://x">y</a>')
        assert_valid_telegram_html(self, html)
        self.assertNotIn('<a', html)
        self.assertIn('y', html)


class TestSupportedTags(unittest.TestCase):
    def test_markdown_conversions(self):
        cases = {
            '**b**': '<b>b</b>',
            '*i*': '<i>i</i>',
            '__u__': '<u>u</u>',
            '~~s~~': '<s>s</s>',
            '`c`': '<code>c</code>',
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(prepare_content_for_telegram(source), expected)

    def test_supported_html_is_kept(self):
        html = prepare_content_for_telegram('<b>negrita</b> <i>cursiva</i> <u>sub</u>')
        self.assertEqual(html, '<b>negrita</b> <i>cursiva</i> <u>sub</u>')
        assert_valid_telegram_html(self, html)

    def test_strong_em_ins_del_normalize(self):
        html = prepare_content_for_telegram('<strong>a</strong><em>b</em><ins>c</ins><del>d</del>')
        self.assertEqual(html, '<b>a</b><i>b</i><u>c</u><s>d</s>')
        assert_valid_telegram_html(self, html)

    def test_spoiler_variants(self):
        html = prepare_content_for_telegram('||secreto||')
        self.assertEqual(html, '<tg-spoiler>secreto</tg-spoiler>')
        html = prepare_content_for_telegram('<span class="tg-spoiler">s</span>')
        self.assertEqual(html, '<tg-spoiler>s</tg-spoiler>')

    def test_blockquote(self):
        html = prepare_content_for_telegram('> cita\n> mas')
        self.assertEqual(html, '<blockquote>cita\nmas</blockquote>')
        assert_valid_telegram_html(self, html)

    def test_pre_code_block(self):
        html = prepare_content_for_telegram('```\nprint(1)\n```')
        self.assertEqual(html, '<pre><code>print(1)</code></pre>')
        assert_valid_telegram_html(self, html)

    def test_pre_code_block_with_language(self):
        html = prepare_content_for_telegram('```python\nprint(1)\n```')
        self.assertEqual(html, '<pre><code class="language-python">print(1)</code></pre>')
        assert_valid_telegram_html(self, html)

    def test_code_tag_with_language_class_is_kept(self):
        html = prepare_content_for_telegram('<pre><code class="language-py">x</code></pre>')
        self.assertEqual(html, '<pre><code class="language-py">x</code></pre>')
        assert_valid_telegram_html(self, html)

    def test_code_tag_drops_unknown_class(self):
        html = prepare_content_for_telegram('<code class="not-a-language">x</code>')
        self.assertEqual(html, '<code>x</code>')

    def test_expandable_blockquote(self):
        html = prepare_content_for_telegram('<blockquote expandable>cita</blockquote>')
        self.assertEqual(html, '<blockquote expandable>cita</blockquote>')
        assert_valid_telegram_html(self, html)

    def test_tg_time(self):
        html = prepare_content_for_telegram(
            '<tg-time unix="1647531900" format="wDT">22:45</tg-time>'
        )
        self.assertEqual(
            html, '<tg-time unix="1647531900" format="wDT">22:45</tg-time>'
        )
        assert_valid_telegram_html(self, html)

    def test_tg_time_without_format(self):
        html = prepare_content_for_telegram('<tg-time unix="1647531900">22:45</tg-time>')
        self.assertEqual(html, '<tg-time unix="1647531900">22:45</tg-time>')

    def test_tg_time_with_non_numeric_unix_is_not_a_live_tag(self):
        html = prepare_content_for_telegram('<tg-time unix="abc">22:45</tg-time>')
        assert_valid_telegram_html(self, html)
        self.assertNotIn('<tg-time', html)
        self.assertIn('22:45', html)

    def test_custom_emoji(self):
        html = prepare_content_for_telegram('<tg-emoji emoji-id="5368324170671202286">\U0001f44d</tg-emoji>')
        self.assertIn('tg-emoji', html)
        assert_valid_telegram_html(self, html)

    def test_bare_url_becomes_link(self):
        html = prepare_content_for_telegram('ver https://t.me/canal')
        self.assertIn('<a href="https://t.me/canal">', html)
        assert_valid_telegram_html(self, html)

    def test_url_query_ampersand_is_escaped_inside_href(self):
        html = prepare_content_for_telegram('https://t.me/x?a=1&b=2')
        self.assertIn('href="https://t.me/x?a=1&amp;b=2"', html)
        assert_valid_telegram_html(self, html)

    def test_bullets_are_normalized(self):
        html = prepare_content_for_telegram('- uno\n* dos')
        self.assertEqual(html, '\u2022 uno\n\u2022 dos')


class TestUnbalancedInput(unittest.TestCase):
    def test_unopened_closing_tag_stays_balanced(self):
        html = prepare_content_for_telegram('</b>texto')
        assert_valid_telegram_html(self, html)
        self.assertEqual(html, '&lt;/b&gt;texto')

    def test_crossed_tags_never_leak_markup(self):
        html = prepare_content_for_telegram('<b><i>x</b>')
        assert_valid_telegram_html(self, html)

    def test_unclosed_opening_tag_is_closed(self):
        html = prepare_content_for_telegram('<b>texto')
        self.assertEqual(html, '<b>texto</b>')
        assert_valid_telegram_html(self, html)

    def test_unfinished_markdown_is_literal(self):
        self.assertEqual(prepare_content_for_telegram('**sin cerrar'), '**sin cerrar')

    def test_math_asterisks_are_not_italic(self):
        self.assertEqual(prepare_content_for_telegram('3 * 4 * 5'), '3 * 4 * 5')

    def test_underscores_inside_words_are_literal(self):
        self.assertEqual(prepare_content_for_telegram('under_score_here'), 'under_score_here')

    def test_empty_input(self):
        self.assertEqual(prepare_content_for_telegram(''), '')
        self.assertEqual(prepare_content_for_telegram(None), '')


class TestLimits(unittest.TestCase):
    def test_clamp_respects_caption_limit(self):
        html = prepare_content_for_telegram('<b>' + 'a' * 3000 + '</b>')
        clamped = clamp_telegram_text(html, TELEGRAM_CAPTION_LIMIT)
        assert_valid_telegram_html(self, clamped, TELEGRAM_CAPTION_LIMIT)
        self.assertLessEqual(len(clamped), TELEGRAM_CAPTION_LIMIT)

    def test_clamp_never_exceeds_limit(self):
        for limit in (10, 20, 64, 200, 1024):
            for source in ('a' * 5000, '<b>' + 'a' * 5000 + '</b>', '<i>x</i>' * 900):
                clamped = clamp_telegram_text(prepare_content_for_telegram(source), limit)
                self.assertLessEqual(len(clamped), limit, f'limit={limit}')

    def test_clamp_leaves_short_text_untouched(self):
        self.assertEqual(clamp_telegram_text('hola', 1024), 'hola')

    def test_split_produces_valid_chunks(self):
        html = prepare_content_for_telegram('**linea de texto**\n' * 900)
        chunks = split_telegram_text(html)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            assert_valid_telegram_html(self, chunk)

    def test_split_single_giant_word(self):
        chunks = split_telegram_text('a' * 9000)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), TELEGRAM_TEXT_LIMIT)
        self.assertEqual(''.join(chunks), 'a' * 9000)

    def test_split_short_text_is_one_chunk(self):
        self.assertEqual(split_telegram_text('<b>hola</b>'), ['<b>hola</b>'])

    def test_split_empty(self):
        self.assertEqual(split_telegram_text(''), [])

    def test_visible_length_excludes_markup(self):
        self.assertEqual(visible_length('<b>hola</b>'), 4)
        self.assertEqual(visible_length('a &lt; b'), 5)


class TestBuildPostContent(unittest.TestCase):
    def test_title_is_bold_and_separated_by_blank_line(self):
        html = build_post_content('Mi Titulo', 'el cuerpo')
        self.assertEqual(html, '<b>Mi Titulo</b>\n\nel cuerpo')
        assert_valid_telegram_html(self, html)

    def test_title_is_escaped(self):
        html = build_post_content('A & B', 'cuerpo')
        self.assertEqual(html, '<b>A &amp; B</b>\n\ncuerpo')
        assert_valid_telegram_html(self, html)

    def test_cta_and_hashtags_on_consecutive_lines(self):
        html = build_post_content('T', 'cuerpo', 'Compra ya', '#uno #dos')
        self.assertEqual(html, '<b>T</b>\n\ncuerpo\n\nCompra ya\n#uno #dos')
        assert_valid_telegram_html(self, html)

    def test_missing_parts_are_omitted(self):
        self.assertEqual(build_post_content('', 'solo cuerpo'), 'solo cuerpo')
        self.assertEqual(build_post_content('', ''), '')


if __name__ == '__main__':
    unittest.main(verbosity=2)
