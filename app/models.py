from . import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Idoso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    data_nascimento = db.Column(db.String(10), nullable=False)
    endereco = db.Column(db.String(200), nullable=False)
    contato_responsavel = db.Column(db.String(100), nullable=False)
    condicoes_medicas = db.Column(db.Text)
    medicamentos = db.Column(db.Text)
    ultima_avaliacao = db.Column(db.String(10))

    @property
    def idade(self):
        from datetime import date, datetime
        hoje = date.today()
        nascimento = datetime.strptime(self.data_nascimento, "%Y-%m-%d").date()
        return hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))
    
class MonitoramentoSaude(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    idoso_id = db.Column(db.Integer, db.ForeignKey('idoso.id'), nullable=False)
    data_registro = db.Column(db.String(10), nullable=False)
    temperatura = db.Column(db.Float)
    pressao = db.Column(db.String(20))
    batimentos = db.Column(db.Integer)
    observacoes = db.Column(db.Text)
    profissional = db.Column(db.String(100))

    idoso = db.relationship('Idoso', backref=db.backref('monitoramentos', lazy=True))

