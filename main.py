import sqlite3
from datetime import datetime
from pathlib import Path


PASTA = Path(__file__).parent
ARQUIVO_BANCO = PASTA / 'almoxarifado.db'


def conectar():
    conexao = sqlite3.connect(ARQUIVO_BANCO)
    conexao.execute('PRAGMA foreign_keys = ON')
    return conexao


def iniciar_banco():
    with conectar() as conexao:
        script = (PASTA / 'banco.sql').read_text(encoding='utf-8')
        conexao.executescript(script)


def ler_numero(mensagem, minimo=None):
    while True:
        try:
            numero = int(input(mensagem))
            if minimo is not None and numero < minimo:
                print(f'digite um numero maior ou igual a {minimo}.')
                continue
            return numero
        except ValueError:
            print('digite um numero inteiro valido.')


def ler_valor(mensagem):
    while True:
        try:
            valor = float(input(mensagem).replace(',', '.'))
            if valor <= 0:
                print('o valor unitario precisa ser maior que zero.')
                continue
            return valor
        except ValueError:
            print('digite um valor valido.')


def ler_data(mensagem):
    while True:
        data = input(mensagem + ' (AAAA-MM-DD): ').strip()
        try:
            datetime.strptime(data, '%Y-%m-%d')
            return data
        except ValueError:
            print('data invalida. use o formato AAAA-MM-DD.')


def listar_produtos():
    with conectar() as conexao:
        produtos = conexao.execute(
            'SELECT id, nome, categoria, unidade_medida, quantidade, valor_unitario '
            'FROM produtos ORDER BY nome'
        ).fetchall()

    print('\nPRODUTOS')
    for produto in produtos:
        print(
            f'ID {produto[0]} | {produto[1]} | {produto[2]} | '
            f'{produto[3]} | estoque: {produto[4]} | R$ {produto[5]:.2f}'
        )


def total_por_categoria():
    with conectar() as conexao:
        categorias = conexao.execute(
            'SELECT categoria, SUM(valor_total) FROM vw_estoque '
            'GROUP BY categoria ORDER BY categoria'
        ).fetchall()

    print('\nVALOR TOTAL POR CATEGORIA')
    for categoria, total in categorias:
        print(f'{categoria}: R$ {total:.2f}')


def cadastrar_produto():
    nome = input('nome do produto: ').strip()
    categoria = input('categoria: ').strip()
    unidade = input('unidade de medida (ex.: litro, pacote): ').strip()

    if not categoria:
        print('a categoria nao pode ficar vazia.')
        return
    if not nome or not unidade:
        print('nome e unidade de medida sao obrigatorios.')
        return

    quantidade = ler_numero('Quantidade inicial (0 a 100): ', 0)
    while quantidade > 100:
        print('o estoque maximo e 100 unidades.')
        quantidade = ler_numero('quantidade inicial (0 a 100): ', 0)
    valor = ler_valor('valor unitario: R$ ')

    with conectar() as conexao:
        conexao.execute(
            'INSERT INTO produtos (nome, categoria, unidade_medida, quantidade, valor_unitario) '
            'VALUES (?, ?, ?, ?, ?)',
            (nome, categoria, unidade, quantidade, valor),
        )
    print('produto cadastrado.')


def registrar_entrada():
    produto_id = ler_numero('ID do produto: ', 1)
    quantidade = ler_numero('Quantidade que entrou: ', 1)
    data = ler_data('Data da entrada')

    with conectar() as conexao:
        produto = conexao.execute(
            'SELECT quantidade FROM produtos WHERE id = ?', (produto_id,)
        ).fetchone()
        if produto is None:
            print('Produto nao encontrado.')
            return
        novo_estoque = produto[0] + quantidade
        if novo_estoque > 100:
            print('A entrada ultrapassa o limite maximo de 100 unidades.')
            return
        conexao.execute(
            'INSERT INTO entradas (produto_id, quantidade, data_entrada) VALUES (?, ?, ?)',
            (produto_id, quantidade, data),
        )
        conexao.execute(
            'UPDATE produtos SET quantidade = ? WHERE id = ?',
            (novo_estoque, produto_id),
        )
    print('entrada registrada e estoque atualizado')


def registrar_saida():
    produto_id = ler_numero('ID do produto: ', 1)
    quantidade = ler_numero('Quantidade que saiu: ', 1)
    data = ler_data('Data da saida')

    with conectar() as conexao:
        produto = conexao.execute(
            'SELECT quantidade FROM produtos WHERE id = ?', (produto_id,)
        ).fetchone()
        if produto is None:
            print('Produto nao encontrado.')
            return
        if quantidade > produto[0]:
            print('Nao ha estoque suficiente para essa saida.')
            return
        conexao.execute(
            'INSERT INTO saidas (produto_id, quantidade, data_saida) VALUES (?, ?, ?)',
            (produto_id, quantidade, data),
        )
        conexao.execute(
            'UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?',
            (quantidade, produto_id),
        )
    print('Saida registrada e estoque atualizado.')


def listar_saidas():
    with conectar() as conexao:
        saidas = conexao.execute(
            'SELECT p.nome, s.quantidade, s.data_saida '
            'FROM saidas s JOIN produtos p ON p.id = s.produto_id '
            'ORDER BY s.data_saida DESC'
        ).fetchall()

    print('\nSAIDAS (mais recentes primeiro)')
    for nome, quantidade, data in saidas:
        print(f'{data} | {nome} | quantidade: {quantidade}')


def ler_periodo():
    data_inicial = ler_data('Data inicial')
    data_final = ler_data('Data final')
    while data_final < data_inicial:
        print('A data final nao pode ser anterior a data inicial.')
        data_final = ler_data('Data final')
    return data_inicial, data_final


def relatorio_movimentacoes():
    data_inicial, data_final = ler_periodo()
    with conectar() as conexao:
        dados = conexao.execute(
            '''
            SELECT p.nome, p.unidade_medida,
                COALESCE(e.total, 0), COALESCE(s.total, 0),
                COALESCE(e.total, 0) - COALESCE(s.total, 0),
                COALESCE(e.financeiro, 0), COALESCE(s.financeiro, 0)
            FROM produtos p
            LEFT JOIN (
                SELECT produto_id, SUM(quantidade) AS total,
                    SUM(quantidade * (SELECT valor_unitario FROM produtos WHERE id = produto_id)) AS financeiro
                FROM entradas
                WHERE data_entrada BETWEEN ? AND ?
                GROUP BY produto_id
            ) e ON e.produto_id = p.id
            LEFT JOIN (
                SELECT produto_id, SUM(quantidade) AS total,
                    SUM(quantidade * (SELECT valor_unitario FROM produtos WHERE id = produto_id)) AS financeiro
                FROM saidas
                WHERE data_saida BETWEEN ? AND ?
                GROUP BY produto_id
            ) s ON s.produto_id = p.id
            ORDER BY p.nome
            ''',
            (data_inicial, data_final, data_inicial, data_final),
        ).fetchall()

    print('\nMOVIMENTACOES NO PERIODO')
    print('Produto | Unidade | Entradas | Saidas | Saldo | R$ entradas | R$ saidas')
    for linha in dados:
        print(
            f'{linha[0]} | {linha[1]} | {linha[2]} | {linha[3]} | {linha[4]} | '
            f'R$ {linha[5]:.2f} | R$ {linha[6]:.2f}'
        )


def relatorio_maiores_saidas():
    data_inicial, data_final = ler_periodo()
    with conectar() as conexao:
        dados = conexao.execute(
            '''
            SELECT p.nome, SUM(s.quantidade), SUM(s.quantidade * p.valor_unitario)
            FROM saidas s JOIN produtos p ON p.id = s.produto_id
            WHERE s.data_saida BETWEEN ? AND ?
            GROUP BY p.id, p.nome
            ORDER BY SUM(s.quantidade) DESC
            ''',
            (data_inicial, data_final),
        ).fetchall()

    print('\nPRODUTOS COM MAIORES SAIDAS')
    print('Produto | Quantidade total de saida | Valor financeiro')
    for nome, quantidade, valor in dados:
        print(f'{nome} | {quantidade} | R$ {valor:.2f}')
    if not dados:
        print('Nenhuma saida encontrada nesse periodo.')


def produtos_nos_limites():
    with conectar() as conexao:
        produtos = conexao.execute(
            'SELECT nome, quantidade FROM produtos WHERE quantidade = 0 OR quantidade = 100 '
            'ORDER BY nome'
        ).fetchall()

    print('\nPRODUTOS NOS LIMITES DO ESTOQUE (minimo 0, maximo 100)')
    if not produtos:
        print('Nenhum produto atingiu os limites.')
    for nome, quantidade in produtos:
        percentual = quantidade / 100 * 100
        limite = 'minimo' if quantidade == 0 else 'maximo'
        print(f'{nome} | limite {limite} | nivel atingido: {percentual:.1f}%')


def menu():
    iniciar_banco()
    while True:
        print(
            '\n=== CONTROLE DO ALMOXARIFADO ===\n'
            '1 - Listar produtos\n'
            '2 - Valor total por categoria\n'
            '3 - Cadastrar produto\n'
            '4 - Registrar entrada\n'
            '5 - Registrar saida\n'
            '6 - Listar saidas\n'
            '7 - Relatorio de movimentacoes por periodo\n'
            '8 - Produtos com maiores saidas no periodo\n'
            '9 - Produtos nos limites do estoque\n'
            '0 - Sair'
        )
        opcao = input('escolha: ').strip()

        if opcao == '1':
            listar_produtos()
        elif opcao == '2':
            total_por_categoria()
        elif opcao == '3':
            cadastrar_produto()
        elif opcao == '4':
            registrar_entrada()
        elif opcao == '5':
            registrar_saida()
        elif opcao == '6':
            listar_saidas()
        elif opcao == '7':
            relatorio_movimentacoes()
        elif opcao == '8':
            relatorio_maiores_saidas()
        elif opcao == '9':
            produtos_nos_limites()
        elif opcao == '0':
            print('programa encerrado.')
            break
        else:
            print('opcao invalida.')


if __name__ == '__main__':
    menu()