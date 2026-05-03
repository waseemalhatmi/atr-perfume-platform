from app.extensions import db

class Setting(db.Model):
    __tablename__ = "settings"
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text)
    description = db.Column(db.String(255))
    
    def __repr__(self):
        return f"<Setting {self.key}>"
