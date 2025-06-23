from core.database import Database
from data.models import Title, Image, Post, UserEvent

class Repository:
    def __init__(self, db: Database = None):
        self.db = db or Database()

    # TÍTULOS
    def add_title(self, name: str):
        session = self.db.get_session()
        try:
            title = Title(name=name)
            session.add(title)
            session.commit()
            return title.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_titles(self):
        session = self.db.get_session()
        try:
            return session.query(Title).all()
        finally:
            session.close()

    def update_title(self, title_id: int, new_name: str):
        session = self.db.get_session()
        try:
            title = session.query(Title).get(title_id)
            if title:
                title.name = new_name
                session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_title(self, title_id: int):
        session = self.db.get_session()
        try:
            title = session.query(Title).get(title_id)
            if title:
                session.delete(title)
                session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # IMÁGENES
    def add_image(self, title_id: int, path: str, keywords: str = None, tone: str = None):
        session = self.db.get_session()
        try:
            image = Image(title_id=title_id, path=path, keywords=keywords, tone=tone)
            session.add(image)
            session.commit()
            return image.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_images_by_title(self, title_id: int):
        session = self.db.get_session()
        try:
            return session.query(Image).filter_by(title_id=title_id).all()
        finally:
            session.close()

    def get_all_images(self):
        session = self.db.get_session()
        try:
            return session.query(Image).all()
        finally:
            session.close()

    # POSTS
    def add_post(self, title_id: int, content: str, image_path: str = None, schedule_time=None):
        session = self.db.get_session()
        try:
            post = Post(title_id=title_id, content=content, image_path=image_path, schedule_time=schedule_time)
            session.add(post)
            session.commit()
            return post.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def record_post(self, title, image_path, content, schedule_time):
        """
        Registra una publicación completa en la base de datos.
        Busca el título por nombre y usa su id.
        """
        session = self.db.get_session()
        try:
            title_obj = session.query(Title).filter_by(name=title).first()
            if not title_obj:
                raise ValueError(f"Título '{title}' no encontrado en la base de datos.")
            post = Post(
                title_id=title_obj.id,
                image_path=image_path,
                content=content,
                schedule_time=schedule_time
            )
            session.add(post)
            session.commit()
            return post.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # EVENTOS DE USUARIO
    def add_user_event(self, event_type: str, timestamp: str):
        session = self.db.get_session()
        try:
            event = UserEvent(event_type=event_type, timestamp=timestamp)
            session.add(event)
            session.commit()
            return event.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_user_events(self):
        session = self.db.get_session()
        try:
            return session.query(UserEvent).all()
        finally:
            session.close()