from app import app, db, Project

with app.app_context():
    cols = [c.name for c in Project.__table__.columns]
    print('Project table columns:', cols)
    cnt = db.session.query(Project).count()
    print('Project row count:', cnt)
