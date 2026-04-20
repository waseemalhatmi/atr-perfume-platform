from app import create_app
from app.models import db

app = create_app()

with app.app_context():
    print("Connecting to the database...")
    # This will create all the tables in Supabase based on your models!
    db.create_all()
    print("Migration successful! All tables have been built in Supabase.")
