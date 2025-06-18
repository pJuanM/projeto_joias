from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "chave_secreta_supersegura"  # Chave para mensagens flash (requerida pelo Flask)

# Nome do banco de dados
DB_NAME = 'db.sqlite'

# Função para conectar ao banco de dados
def db_connection():
    """
    Cria e retorna uma conexão com o banco de dados.
    Define `row_factory` como `sqlite3.Row` para permitir acesso aos resultados como dicionários.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# Função para criar tabelas, caso não existam
def criar_tabelas():
    """
    Cria as tabelas `clientes`, `pedidos` e `pagamentos` no banco de dados se elas não existirem.
    """
    conn = db_connection()
    cursor = conn.cursor()

    # Tabela de clientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT NOT NULL,
            cpf TEXT NOT NULL UNIQUE
        );
    """)

    # Tabela de pedidos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            forma_pagamento TEXT CHECK(forma_pagamento IN ('Dinheiro', 'PIX', 'Cartão')),
            parcelas INTEGER DEFAULT 1,
            valor_pago REAL DEFAULT 0,
            data_pedido TEXT NOT NULL,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        );
    """)

    # Tabela de Itens do pedido
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            cor_pano TEXT CHECK(cor_pano IN ('Preto', 'Vermelho')),
            quantidade INTEGER NOT NULL,
            valor_unitario REAL NOT NULL,
            total REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id)
        );
    """)

    # Tabela de pagamentos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pagamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            valor_pago REAL NOT NULL,
            data_pagamento TEXT NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id)
        );
    """)

    conn.commit()
    conn.close()

# Rota principal (página inicial)
@app.route('/')
def index():
    """
    Renderiza a página inicial do sistema.
    """
    return render_template("index.html")

# ---- CLIENTES ----
@app.route('/clientes')
def clientes():
    """
    Exibe a lista de clientes cadastrados, ordenados pelo ID.
    """
    conn = db_connection()
    clientes = conn.execute("SELECT * FROM clientes ORDER BY id").fetchall()
    conn.close()
    return render_template("clientes.html", clientes=clientes)
@app.route('/clientes/novo', methods=['GET', 'POST'])
def novo_cliente():
    """
    Permite o cadastro de um novo cliente.
    Verifica se todos os campos estão preenchidos e se o CPF é único.
    """
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        telefone = request.form['telefone'].strip()
        cpf = request.form['cpf'].strip()

        if not nome or not telefone or not cpf:
            flash("Preencha todos os campos", "error")
            return redirect(url_for("novo_cliente"))

        try:
            conn = db_connection()
            conn.execute("INSERT INTO clientes (nome, telefone, cpf) VALUES (?, ?, ?)", (nome, telefone, cpf))
            conn.commit()
            flash("Cliente cadastrado com sucesso!", "success")
        except sqlite3.IntegrityError:
            flash("Este CPF já foi cadastrado!", "error")
            return redirect(url_for("novo_cliente"))
        finally:
            conn.close()

        return redirect(url_for("clientes"))

    return render_template("novo_cliente.html")
@app.route('/clientes/<int:cliente_id>')
def detalhes_cliente(cliente_id):
    conn = db_connection()
    cursor = conn.cursor()

    # Dados do cliente
    cliente = cursor.execute(""" 
        SELECT
            clientes.id, clientes.nome, clientes.telefone, clientes.cpf
        FROM clientes
        WHERE clientes.id = ?; 
    """, (cliente_id,)).fetchone()

    conn.close()

    if not cliente:
        return jsonify({"erro": "Cliente não encontrado"}), 404
    
    return jsonify({
        "id": cliente["id"],
        "nome":cliente["nome"],
        "telefone":cliente["telefone"],
        "cpf":cliente["cpf"]
    })


# ---- PEDIDOS ----
@app.route('/pedidos')
def pedidos():
    """
    Exibe a lista de pedidos, com informações adicionais do cliente associado.
    """
    conn = db_connection()
    pedidos = conn.execute("""
        SELECT pedidos.id,
                           clientes.nome AS cliente_nome, 
                           pedidos.forma_pagamento, 
                           pedidos.parcelas,
                           pedidos.data_pedido,
                           COALESCE(SUM(itens_pedido.total), 0) AS total
        FROM pedidos
        JOIN clientes ON pedidos.cliente_id = clientes.id
        LEFT JOIN itens_pedido ON pedidos.id = itens_pedido.pedido_id
        GROUP BY pedidos.id
        ORDER BY pedidos.data_pedido DESC;
    """).fetchall()
    conn.close()
    return render_template("pedidos.html", pedidos=pedidos)

@app.route('/pedidos/<int:pedido_id>')
def detalhes_pedido(pedido_id):
    conn = db_connection()
    cursor = conn.cursor()

    # Dados do cliente e do pedido
    pedido = cursor.execute("""
        SELECT 
            pedidos.id, 
            pedidos.data_pedido, 
            clientes.nome, 
            clientes.telefone, 
            clientes.cpf
        FROM pedidos
        JOIN clientes ON pedidos.cliente_id = clientes.id
        WHERE pedidos.id = ?;
    """, (pedido_id,)).fetchone()

    # Itens do pedido
    itens = cursor.execute(""" 
                SELECT 
                    itens_pedido.descricao,
                    itens_pedido.cor_pano,
                    itens_pedido.valor_unitario,
                    itens_pedido.quantidade, 
                    itens_pedido.total
                FROM itens_pedido
                WHERE itens_pedido.pedido_id = ?;
    """, (pedido_id,)).fetchall()
    
    conn.close()
    # Verifica se a variável pedido está vazia (None). 
    # Se estiver, significa que não existe pedido com aquele pedido_id no banco. 
    # Então a API responde com um JSON de erro e código HTTP 404 (não encontrado).
    if not pedido:
        return jsonify({"erro": "Pedido não encontrado"}), 404
    # Se o pedido foi encontrado, retorna os dados em formato JSON.
    # O pedido foi obtido via fetchone() e é uma tupla. Aqui, estamos acessando por índice:
    return jsonify({
        "id": pedido["id"],
        "data_pedido": pedido["data_pedido"],
        "cliente": {
            "nome": pedido["nome"],
            "telefone": pedido["telefone"],
            "cpf": pedido["cpf"]
        },
        # A variável itens contém uma lista de tuplas com os itens do pedido. Para cada item, é criado um dicionário com:
        "itens": [
            {
                "nome": item["descricao"],
                "cor_pano":item["cor_pano"],
                "valor_unitario": item["valor_unitario"],
                "quantidade": item["quantidade"],
                "total":item["total"]
            } for item in itens
        ]
    })

@app.route('/pedidos/novo', methods=['GET', 'POST'])
def novo_pedido():
    """
    Permite o cadastro de um novo pedido.
    Realiza validações nos campos e calcula o total com base na quantidade e valor unitário.
    """
    conn = db_connection()
    clientes = conn.execute("SELECT * FROM clientes ORDER BY nome").fetchall()

    if request.method == 'POST':
        # Dados gerais do pedido
        cliente_id = request.form.get('cliente_id').strip()
        forma_pagamento = request.form.get('forma_pagamento').strip()
        parcelas = request.form.get('parcelas').strip()

        # Dados dos itens do pedido
        descricoes = request.form.getlist('descricao')
        cores_pano = request.form.getlist('cor_pano')
        quantidades = request.form.getlist('quantidade')
        valores_unitarios = request.form.getlist('valor_unitario')

        # Validações
        erros = []
        if not cliente_id:
            erros.append("Cliente é obrigatório")
        if forma_pagamento not in ["Dinheiro", "PIX", "Cartão"]:
            erros.append("Selecione a forma de pagamento")
        try:
            parcelas = int(parcelas)
            if parcelas <= 0:
                erros.append("Parcelas deve ser maior que zero")
        except:
            erros.append("Número de parcelas inválido")

        itens = []
        for i in range(len(descricoes)):
            descricao = descricoes[i].strip()
            cor_pano = cores_pano[i].strip()
            try:
                quantidade = int(quantidades[i])
                valor_unitario = float(valores_unitarios[i])
                if quantidade <= 0 or valor_unitario <= 0:
                    raise ValueError
            except:
                erros.append(f"Quantidade ou valor inválido no item {i + 1}")
                continue
            total_item = quantidade * valor_unitario
            itens.append((descricao, cor_pano, quantidade, valor_unitario, total_item))

        if erros:
            for e in erros:
                flash(e, "error")
            conn.close()
            return redirect(url_for("novo_pedido"))

        # Inserir o pedido na tabela `pedidos`
        data_pedido = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute("""
            INSERT INTO pedidos (cliente_id, forma_pagamento, parcelas, valor_pago, data_pedido)
            VALUES (?, ?, ?, 0, ?)
        """, (cliente_id, forma_pagamento, parcelas, data_pedido))
        pedido_id = cursor.lastrowid

        # Inserir os itens na tabela `itens_pedido`
        for item in itens:
            conn.execute("""
                INSERT INTO itens_pedido (pedido_id, descricao, cor_pano, quantidade, valor_unitario, total)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (pedido_id, *item))

        conn.commit()
        conn.close()
        flash("Pedido cadastrado com sucesso!", "success")
        return redirect(url_for("pedidos"))

    return render_template("novo_pedido.html", clientes=clientes)


# ---- PAGAMENTOS ----

@app.route('/pagamentos')
def pagamentos():
    """
    Exibe a lista de pagamentos realizados e os pedidos com saldo pendente.
    """
    conn = db_connection()

    # Busca todos os pagamentos com informações adicionais de pedidos e clientes
    pagamentos = conn.execute("""
        SELECT pagamentos.*, clientes.nome as cliente_nome, pedidos.id as pedido_id
        FROM pagamentos
        JOIN pedidos ON pagamentos.pedido_id = pedidos.id
        JOIN clientes ON pedidos.cliente_id = clientes.id
        ORDER BY pagamentos.data_pagamento
    """).fetchall()

    # Busca pedidos com saldo pendente para novos pagamentos
    pedidos = conn.execute("""
        SELECT pedidos.id, clientes.nome as cliente_nome,
               pedidos.valor_pago, 
               (SELECT SUM(total) FROM itens_pedido WHERE pedido_id = pedidos.id) as total,
               ((SELECT SUM(total) FROM itens_pedido WHERE pedido_id = pedidos.id) - pedidos.valor_pago) as saldo_pendente
        FROM pedidos
        JOIN clientes ON pedidos.cliente_id = clientes.id
        WHERE ((SELECT SUM(total) FROM itens_pedido WHERE pedido_id = pedidos.id) - pedidos.valor_pago) > 0
        ORDER BY pedidos.data_pedido
    """).fetchall()
    conn.close()
    return render_template("pagamentos.html", pagamentos=pagamentos, pedidos=pedidos)
@app.route('/pagamentos/novo', methods=['POST'])
def novo_pagamento():
    """
    Permite registrar um novo pagamento para um pedido.
    Valida o valor pago e atualiza o saldo pendente no banco.
    """
    # Obtém os dados do formulário
    pedido_id = request.form.get('pedido_id')
    valor_pago = request.form.get('valor_pago')

    try:
        valor_pago = float(valor_pago)
        if valor_pago <= 0:
            flash("O valor pago deve ser maior que zero.", "error")
            return redirect(url_for('pagamentos'))
    except ValueError:
        flash("Valor pago inválido.", "error")
        return redirect(url_for('pagamentos'))

    conn = db_connection()

    # Verifica o saldo pendente do pedido
    pedido = conn.execute("""
        SELECT 
            (SELECT SUM(total) FROM itens_pedido WHERE pedido_id = pedidos.id) AS total,
            valor_pago
        FROM pedidos WHERE id = ?
    """, (pedido_id,)).fetchone()
    
    if not pedido:
        flash("Pedido não encontrado.", "error")
        conn.close()
        return redirect(url_for('pagamentos'))

    saldo_pendente = (pedido['total'] or 0) - (pedido['valor_pago'] or 0)
    if valor_pago > saldo_pendente:
        flash(f"Valor maior que o saldo pendente", "error")
        conn.close()
        return redirect(url_for('pagamentos'))

    # Registra o pagamento e atualiza o valor pago no pedido
    data_pagamento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("""
        INSERT INTO pagamentos (pedido_id, valor_pago, data_pagamento)
        VALUES (?, ?, ?)
    """, (pedido_id, valor_pago, data_pagamento))
    
    novo_valor_pago = pedido['valor_pago'] + valor_pago
    conn.execute("""
        UPDATE pedidos SET valor_pago = ? WHERE id = ?
    """, (novo_valor_pago, pedido_id))

    conn.commit()
    conn.close()

    flash("Pagamento registrado com sucesso!", "success")
    return redirect(url_for("pagamentos"))
@app.route('/pagamentos/<int:pagamento_id>')
def detalhes_pagamento(pagamento_id):
    conn = db_connection()


    # Dados do pagamento
    pagamentos = conn.execute(""" 
        SELECT 
            pagamentos.id, 
            pagamentos.pedido_id, 
            pagamentos.valor_pago, 
            pagamentos.data_pagamento
        FROM pagamentos
        WHERE pagamentos.id = ?;
    """, (pagamento_id,)).fetchone()

    conn.close()
    if not pagamentos:
        return jsonify({"erro":"Pagamento não encontrado"}), 404
    return jsonify({
        "id":pagamentos["id"],
        "pedido":pagamentos["pedido_id"],
        "valor_pago":pagamentos["valor_pago"],
        "data_pagamento":pagamentos["data_pagamento"]
    })
# ---- RELATÓRIOS ----

@app.route('/relatorios')
def relatorios():
    """
    Gera relatórios financeiros simples:
    - Total de vendas
    - Total recebido
    - Total pendente
    """
    conn = db_connection()

    # Soma do total de vendas (calcula a soma da quantidade * valor_unitario na tabela itens_pedido)
    vendas = conn.execute("""
        SELECT COALESCE(SUM(quantidade * valor_unitario), 0) as total FROM itens_pedido
    """).fetchone()

    # Soma do valor já recebido
    recebidos = conn.execute("""
        SELECT COALESCE(SUM(valor_pago), 0) as recebido FROM pedidos
    """).fetchone()

    # Calcula o valor pendente
    pendente = vendas['total'] - recebidos['recebido']

    conn.close()
    return render_template("relatorios.html", vendas=vendas, recebidos=recebidos, pendente=pendente)

if __name__ == '__main__':
    # Cria tabelas antes de iniciar o servidor
    criar_tabelas()
    app.run(debug=True)
