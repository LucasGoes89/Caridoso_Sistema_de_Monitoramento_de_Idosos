from flask import Blueprint, render_template, redirect, url_for, request
from .models import db, User, Idoso, MonitoramentoSaude
from werkzeug.security import generate_password_hash
from flask import session
import pandas as pd
from flask import send_file
from io import BytesIO

main = Blueprint('main', __name__)

@main.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    total_idosos = Idoso.query.count()
    total_monitoramentos = MonitoramentoSaude.query.count()
    total_usuarios = User.query.count()  # Conta total de usuários cadastrados

    return render_template(
        'home.html',
        total_idosos=total_idosos,
        total_monitoramentos=total_monitoramentos,
        total_usuarios=total_usuarios  # Passa para o template
    )

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id  # salva o ID na sessão
            session['username'] = user.username
            return redirect(url_for('main.home'))
        else:
            return "Usuário ou senha incorretos!"

    return render_template('login.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            return "Usuário já existe!"

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('main.login'))

    return render_template('register.html')

@main.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('main.login'))

@main.route('/adicionar_idoso')
def adicionar_idoso():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    return render_template('adicionar_idoso.html')

@main.route('/salvar_idoso', methods=['POST'])
def salvar_idoso():
    novo_idoso = Idoso(
        nome=request.form['nome'],
        data_nascimento=request.form['data_nascimento'],
        endereco=request.form['endereco'],
        contato_responsavel=request.form['contato_responsavel'],
        condicoes_medicas=request.form['condicoes_medicas'],
        medicamentos=request.form['medicamentos'],
        ultima_avaliacao=request.form['ultima_avaliacao']
    )
    db.session.add(novo_idoso)
    db.session.commit()
    return redirect(url_for('main.home'))  # ou redirecione para /idosos

@main.route('/idosos')
def listar_idosos():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    idosos = Idoso.query.all()
    return render_template('idosos.html', idosos=idosos)

@main.route('/monitoramento')
def selecionar_idoso_para_monitorar():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    idosos = Idoso.query.all()
    return render_template('selecionar_idoso_monitoramento.html', idosos=idosos)


@main.route('/monitoramento/<int:idoso_id>', methods=['GET'])
def monitoramento_form(idoso_id):
    idoso = Idoso.query.get_or_404(idoso_id)
    return render_template('monitoramento.html', idoso=idoso)

@main.route('/monitoramento/salvar', methods=['POST'])
def salvar_monitoramento():
    novo_monitoramento = MonitoramentoSaude(
        idoso_id=request.form['idoso_id'],
        data_registro=request.form['data_registro'],
        temperatura=request.form['temperatura'],
        pressao=request.form['pressao'],
        batimentos=request.form['batimentos'],
        observacoes=request.form['observacoes'],
        profissional=request.form['profissional']
    )
    db.session.add(novo_monitoramento)
    db.session.commit()
    return redirect(url_for('main.listar_idosos'))  # Ou redirecionar para o histórico do idoso

@main.route('/monitoramento/historico/<int:idoso_id>')
def historico_monitoramento(idoso_id):
    idoso = Idoso.query.get_or_404(idoso_id)
    monitoramentos = MonitoramentoSaude.query.filter_by(idoso_id=idoso_id).order_by(MonitoramentoSaude.data_registro.desc()).all()
    return render_template('historico_monitoramento.html', idoso=idoso, monitoramentos=monitoramentos)

@main.route('/idoso/editar/<int:idoso_id>', methods=['GET', 'POST'])
def editar_idoso(idoso_id):
    idoso = Idoso.query.get_or_404(idoso_id)

    if request.method == 'POST':
        idoso.nome = request.form['nome']
        idoso.data_nascimento = request.form['data_nascimento']
        idoso.endereco = request.form['endereco']
        idoso.contato_responsavel = request.form['contato_responsavel']
        idoso.condicoes_medicas = request.form['condicoes_medicas']
        idoso.medicamentos = request.form['medicamentos']
        idoso.ultima_avaliacao = request.form['ultima_avaliacao']

        db.session.commit()
        return redirect(url_for('main.listar_idosos'))

    return render_template('editar_idoso.html', idoso=idoso)

@main.route('/idoso/remover/<int:idoso_id>', methods=['POST'])
def remover_idoso(idoso_id):
    idoso = Idoso.query.get_or_404(idoso_id)
    db.session.delete(idoso)
    db.session.commit()
    return redirect(url_for('main.listar_idosos'))

@main.route('/configuracoes', methods=['GET', 'POST'])
def configuracoes():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    mensagem = ''
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        # Verifica se está alterando a senha
        if 'senha_atual' in request.form and 'nova_senha' in request.form:
            senha_atual = request.form['senha_atual']
            nova_senha = request.form['nova_senha']

            if user and user.check_password(senha_atual):
                user.set_password(nova_senha)
                db.session.commit()
                mensagem = 'Senha alterada com sucesso.'
            else:
                mensagem = 'Senha atual incorreta.'

        # Verifica se está salvando preferências
        if 'dark_mode' in request.form or 'large_font' in request.form:
            dark_mode = request.form.get('dark_mode') == 'on'
            large_font = request.form.get('large_font') == 'on'
            session['preferences'] = {
                'dark_mode': dark_mode,
                'large_font': large_font
            }
            mensagem = 'Preferências salvas com sucesso.'

    preferencias = session.get('preferences', {'dark_mode': False, 'large_font': False})

    usuarios = User.query.all()  # BUSCA TODOS OS USUÁRIOS

    return render_template(
        'configuracoes.html',
        mensagem=mensagem,
        preferencias=preferencias,
        usuarios=usuarios  # PASSA PARA O TEMPLATE
    )

@main.route('/agenda', methods=['GET', 'POST'])
def agenda():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    # Buscar eventos do banco de dados (pode ser de uma tabela específica)
    compromissos = MonitoramentoSaude.query.all()
    eventos = []

    # Formatando os eventos para o formato esperado pelo FullCalendar
    for compromisso in compromissos:
        eventos.append({
            'title': compromisso.profissional,  # Exemplo: título do compromisso
            'start': compromisso.data_registro,  # Data do compromisso
            'end': compromisso.data_registro,    # Pode ser um campo 'fim' se houver
            'description': compromisso.observacoes,
        })

    return render_template('agenda.html', eventos=eventos)


@main.route('/agenda/adicionar_evento', methods=['POST'])
def adicionar_evento():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    evento_titulo = request.form['titulo']
    evento_data = request.form['data']

    novo_evento = MonitoramentoSaude(
        profissional=evento_titulo,
        data_registro=evento_data
    )
    db.session.add(novo_evento)
    db.session.commit()

    return redirect(url_for('main.agenda'))

@main.route('/agenda/remover_evento/<int:evento_id>', methods=['POST'])
def remover_evento(evento_id):
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    evento = MonitoramentoSaude.query.get_or_404(evento_id)
    db.session.delete(evento)
    db.session.commit()

    return redirect(url_for('main.agenda'))

@main.route('/relatorios', methods=['GET', 'POST'])
def relatorios():
    idosos = Idoso.query.all()
    dados = []
    idoso = None
    data_inicio = None
    data_fim = None

    if request.method == 'POST':
        idoso_id = request.form['idoso']
        data_inicio = request.form['data_inicio']
        data_fim = request.form['data_fim']

        idoso = Idoso.query.get(idoso_id)

        monitoramentos = MonitoramentoSaude.query.filter(
            MonitoramentoSaude.idoso_id == idoso_id,
            MonitoramentoSaude.data_registro >= data_inicio,
            MonitoramentoSaude.data_registro <= data_fim
        ).order_by(MonitoramentoSaude.data_registro.asc()).all()

        for m in monitoramentos:
            dados.append({
                'data_registro': m.data_registro,
                'temperatura': m.temperatura,
                'pressao': m.pressao,
                'batimentos': m.batimentos,
                'profissional': m.profissional,
                'observacoes': m.observacoes
            })

    return render_template(
        'relatorio.html',
        idosos=idosos,
        dados=dados,
        idoso=idoso,
        data_inicio=data_inicio,
        data_fim=data_fim
    )

@main.route('/relatorios/exportar_excel')
def exportar_excel():
    idoso_id = request.args.get('idoso_id')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')

    monitoramentos = MonitoramentoSaude.query.filter(
        MonitoramentoSaude.idoso_id == idoso_id,
        MonitoramentoSaude.data_registro >= data_inicio,
        MonitoramentoSaude.data_registro <= data_fim
    ).order_by(MonitoramentoSaude.data_registro.asc()).all()

    data = [{
        'Data': m.data_registro,
        'Temperatura (°C)': m.temperatura,
        'Pressão': m.pressao,
        'Batimentos': m.batimentos,
        'Profissional': m.profissional,
        'Observações': m.observacoes
    } for m in monitoramentos]

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Relatório')
    output.seek(0)

    return send_file(output,
                     download_name='relatorio_idoso.xlsx',
                     as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
