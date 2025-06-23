from datetime import datetime
from sqlalchemy import func
from data.models import Metric, Post, Title  # Asegúrate de tener estos modelos definidos
from sqlalchemy.orm import joinedload

class MetricsService:
    def __init__(self, db_connection):
        self.db_connection = db_connection
        self.create_metrics_table()

    def create_metrics_table(self):
        from data.models import Base
        Base.metadata.create_all(self.db_connection.engine)

    def record_post_metrics(self, post_id, user_event_id, clicks=0, reactions=0):
        session = self.db_connection.get_session()
        try:
            metric = Metric(
                post_id=post_id,
                user_event_id=user_event_id,
                clicks=clicks,
                reactions=reactions,
                created_at=datetime.now()
            )
            session.add(metric)
            session.commit()
        finally:
            session.close()

    def update_metrics(self, metric_id, clicks=None, reactions=None):
        session = self.db_connection.get_session()
        try:
            metric = session.query(Metric).get(metric_id)
            if metric:
                if clicks is not None:
                    metric.clicks += clicks
                if reactions is not None:
                    metric.reactions += reactions
                session.commit()
        finally:
            session.close()

    def get_metrics(self, post_id=None):
        """
        Si post_id es None, devuelve métricas agregadas por título.
        Si post_id está definido, devuelve métricas solo de ese post.
        """
        session = self.db_connection.get_session()
        try:
            if post_id is not None:
                metrics = (
                    session.query(Metric)
                    .filter_by(post_id=post_id)
                    .all()
                )
                return [
                    {
                        "title": self._get_title_by_post_id(session, m.post_id),
                        "posts": 1,
                        "interactions": m.reactions,
                        "clicks": m.clicks,
                        "created_at": m.created_at
                    }
                    for m in metrics
                ]
            else:
                # Métricas agregadas por título
                results = (
                    session.query(
                        Title.name.label("title"),
                        func.count(Metric.id).label("posts"),
                        func.sum(Metric.reactions).label("interactions"),
                        func.sum(Metric.clicks).label("clicks")
                    )
                    .join(Post, Post.title_id == Title.id)
                    .join(Metric, Metric.post_id == Post.id)
                    .group_by(Title.name)
                    .all()
                )
                return [
                    {
                        "title": r.title,
                        "posts": r.posts or 0,
                        "interactions": r.interactions or 0,
                        "clicks": r.clicks or 0
                    }
                    for r in results
                ]
        finally:
            session.close()

    def _get_title_by_post_id(self, session, post_id):
        post = session.query(Post).get(post_id)
        if post:
            title = session.query(Title).get(post.title_id)
            return title.name if title else ""
        return ""