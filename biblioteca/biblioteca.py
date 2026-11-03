import mysql.connector
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from datetime import date

# CONEXÃO AO BANCO DE DADOS
def conectar():
    try:
        conexao = mysql.connector.connect(
            host="localhost", user="root", password="jpr26", database="biblioteca"
        )
        return conexao

    except mysql.connector.Error:
        print("Não foi possível conectar-se ao banco de dados")
        return None

# --- BOTÕES AÇÕES ---
def salvar_livro(
        campo_titulo, campo_autor, campo_ano, campo_quantidade
):

    titulo = campo_titulo.get().strip()
    autor = campo_autor.get().strip()
    ano = campo_ano.get().strip()
    quantidade = campo_quantidade.get().strip()

    if not titulo or not autor or not ano or not quantidade:
        messagebox.showwarning("Aviso", "Preencha todos os campos.")
        return

    if not ano.isdigit():
        messagebox.showwarning("Aviso", "O ano deve ser um número inteiro.")
        return

    if not quantidade.isdigit() or int(quantidade) <= 0:
        messagebox.showwarning("Aviso", "A quantidade deve ser maior que zero.")
        return

    conexao = conectar()

    if conexao is None:
        messagebox.showerror("Erro", "Não foi possível conectar-se ao banco de dados.")
        return

    cursor = None

    try:
        cursor = conexao.cursor()
        sql = '''INSERT INTO livros (titulo, autor, ano, quantidade) VALUES (%s, %s, %s, %s)'''
        valores = (titulo, autor, int(ano), int(quantidade))
        cursor.execute(sql, valores)
        conexao.commit()

        messagebox.showinfo("Ok", "Livro cadastrado com sucesso.")

        campo_titulo.delete(0, tk.END)
        campo_autor.delete(0, tk.END)
        campo_ano.delete(0, tk.END)
        campo_quantidade.delete(0, tk.END)

    except mysql.connector.Error:
        conexao.rollback()
        messagebox.showerror("Erro", "Não foi possível cadastrar o livro.")

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

def salvar_leitor(campo_nome, campo_cpf, campo_telefone, campo_email):
    nome = campo_nome.get().strip()
    cpf = campo_cpf.get().replace(".", "").replace("-", "").replace(" ", "")
    telefone = campo_telefone.get().strip()
    email = campo_email.get().strip()

    if not nome or not cpf or not telefone or not email:
        messagebox.showwarning("Aviso", "Preencha todos os campos.")
        return

    if len(cpf) != 11 or not cpf.isdigit():
        messagebox.showwarning("Aviso", "O CPF deve possuir 11 dígitos.")
        return

    if cpf_cadastrado(cpf):
        messagebox.showwarning("Aviso", "Esse CPF já está cadastrado.")
        return

    partes = email.split("@")
    if len(partes) != 2 or partes[0] == "" or "." not in partes[1]:
        messagebox.showwarning("Aviso", "Digite um e-mail válido.")
        return

    conexao = conectar()

    if conexao is None:
        messagebox.showerror("Erro", "Não foi possível conectar-se ao banco de dados.")
        return

    cursor = None

    try:
        cursor = conexao.cursor()
        sql =  '''INSERT INTO leitores (nome, cpf, telefone, email) VALUES (%s, %s, %s, %s)'''
        valores = (nome, cpf, telefone, email)
        cursor.execute(sql, valores)
        conexao.commit()

        messagebox.showinfo("Ok", "Leitor cadastrado com sucesso.")

        campo_nome.delete(0, tk.END)
        campo_cpf.delete(0, tk.END)
        campo_telefone.delete(0, tk.END)
        campo_email.delete(0, tk.END)

    except mysql.connector.Error:
        conexao.rollback()
        messagebox.showerror("Erro", "Não foi possível cadastrar o leitor")

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

def registrar_emprestimo(campo_leitor, campo_livro):
    leitor_texto = campo_leitor.get().strip()
    livro_texto = campo_livro.get().strip()

    if not leitor_texto or not livro_texto:
        messagebox.showwarning("Aviso", "Informe o ID do usuário e do livro.")
        return

    if not leitor_texto.isdigit() or not livro_texto.isdigit():
        messagebox.showwarning("Aviso", "Os IDs devem ser números inteiros positivos.")
        return

    id_leitor = int(leitor_texto)
    id_livro = int(livro_texto)

    if id_leitor <= 0 or id_livro <= 0:
        messagebox.showwarning("Aviso", "Os IDs devem ser maiores que zero.")
        return

    conexao = conectar()

    if conexao is None:
        messagebox.showerror("Erro", "Não foi possível conectar-se ao banco de dados.")
        return

    cursor = None

    try:
        cursor = conexao.cursor()

        # Verifica se o usuário existe
        cursor.execute(
            '''SELECT id FROM leitores WHERE id = %s''',
            (id_leitor,)
        )
        usuario = cursor.fetchone()

        if usuario is None:
            messagebox.showerror("Erro", "Leitor não encontrado.")
            return

        # Verifica o limite de empréstimos em aberto
        cursor.execute(
            '''
            SELECT COUNT(*) FROM emprestimos
            WHERE leitor_id = %s AND data_devolucao IS NULL
            ''',
            (id_leitor,)
        )
        total_abertos = cursor.fetchone()[0]

        if total_abertos >= 3:
            messagebox.showwarning("Aviso", "Esse leitor já possui 3 empréstimos em aberto.")
            return

        # Verifica se o livro existe e tem exemplares disponíveis
        cursor.execute(
            '''SELECT quantidade FROM livros WHERE id = %s''',
            (id_livro,)
        )
        livro = cursor.fetchone()

        if livro is None:
            messagebox.showerror("Erro", "Livro não encontrado.")
            return

        if livro[0] <= 0:
            messagebox.showerror("Erro", "Não há exemplares disponíveis.")
            return

        # Impede que o usuário pegue novamente o mesmo livro
        cursor.execute(
            '''
            SELECT COUNT(*) FROM emprestimos
            WHERE leitor_id = %s AND livro_id = %s AND data_devolucao IS NULL
            ''',
            (id_leitor, id_livro)
        )

        if cursor.fetchone()[0] > 0:
            messagebox.showerror("Erro", "O leitor já possui esse livro emprestado.")
            return

        # Registra o empréstimo e atualiza a quantidade
        cursor.execute(
            '''
            INSERT INTO emprestimos (leitor_id, livro_id, data_emprestimo)
            VALUES (%s, %s, %s)
            ''',
            (id_leitor, id_livro, date.today())
        )

        cursor.execute(
            '''
            UPDATE livros
            SET quantidade = quantidade - 1
            WHERE id = %s AND quantidade > 0
            ''',
            (id_livro,)
        )

        if cursor.rowcount == 0:
            conexao.rollback()
            messagebox.showerror("Erro", "Não há exemplares disponíveis.")
            return

        conexao.commit()

        messagebox.showinfo("Ok", "Empréstimo realizado com sucesso.")

        campo_leitor.delete(0, tk.END)
        campo_livro.delete(0, tk.END)

    except mysql.connector.Error:
        conexao.rollback()
        messagebox.showerror("Erro", "Não foi possível realizar o empréstimo."
        )

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

def registrar_devolucao(campo_emprestimo):
    id_texto = campo_emprestimo.get().strip()

    if not id_texto.isdigit() or int(id_texto) <= 0:
        messagebox.showwarning("Aviso", "Informe um ID de empréstimo válido")
        return

    id_emprestimo = int(id_texto)
    conexao = conectar()

    if conexao is None:
        messagebox.showerror("Erro", "Não foi possível conectar-se ao banco de dados")
        return

    cursor = None

    try:
        cursor = conexao.cursor()
        sql = '''SELECT livro_id, data_devolucao FROM emprestimos WHERE id = %s'''

        cursor.execute(sql, (id_emprestimo,))
        emprestimo = cursor.fetchone()

        if emprestimo is None:
            messagebox.showerror("Erro", "Empréstimo não encontrado")
            return

        if emprestimo[1] is not None:
            messagebox.showerror("Erro","Esse empréstimo já foi devolvido")
            return

        id_livro = emprestimo[0]

        cursor.execute('''
        UPDATE emprestimos SET data_devolucao = %s 
        WHERE id = %s AND data_devolucao IS NULL
        ''', (date.today(), id_emprestimo)
        )

        if cursor.rowcount == 0:
            conexao.rollback()
            messagebox.showerror("Erro", "Esse empréstimo já foi devolvido")
            return

        cursor.execute(
            '''UPDATE livros SET quantidade = quantidade + 1 WHERE id = %s''', (id_livro,)
        )

        conexao.commit()
        messagebox.showinfo("Ok", "Devolução registrada com sucesso.")

        campo_emprestimo.delete(0, tk.END)

    except mysql.connector.Error:
        conexao.rollback()
        messagebox.showerror("Erro", "Não foi possível registrar a devolução.")

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

def cpf_cadastrado(cpf):
    conexao = conectar()
    cursor = conexao.cursor()
    sql = '''SELECT COUNT(*) FROM leitores WHERE cpf = %s'''
    cursor.execute(sql, (cpf,))
    resultado = cursor.fetchone()
    cursor.close()
    conexao.close()
    return resultado[0] > 0

# --- TELAS ---
# TELA CADASTRAR LIVRO
def cadastrar_livro():
    tela = tk.Toplevel(janela)
    tela.title("Cadastrar livro")
    tela.geometry("450x400")
    tela.resizable(False, False)

    titulo_tela = tk.Label(
        tela,
        text = "CADASTRAR LIVRO",
        font = ("Arial", 16, "bold"),
    )
    titulo_tela.pack(pady=20)

    formulario = tk.Frame(tela)
    formulario.pack(padx=30, pady=10)

    tk.Label(formulario, text="Título: ").grid(row=0, column=0, sticky="w", pady=8)
    campo_titulo = tk.Entry(formulario, width=35)
    campo_titulo.grid(row=0, column=1, pady=8)

    tk.Label(formulario, text="Autor:").grid(row=1, column=0, sticky="w", pady=8)
    campo_autor = tk.Entry(formulario, width=35)
    campo_autor.grid(row=1, column=1, pady=8)

    tk.Label(formulario, text="Ano de publicação:").grid(row=2, column=0, sticky="w", pady=8)
    campo_ano = tk.Entry(formulario, width=35)
    campo_ano.grid(row=2, column=1, pady=8)

    tk.Label(formulario, text="Quantidade:").grid(row=3, column=0, sticky="w", pady=8)
    campo_quantidade = tk.Entry(formulario, width=35)
    campo_quantidade.grid(row=3, column=1, pady=8)

    botao_salvar = tk.Button(
        tela,
        text="Salvar",
        width=20,
        height=2,
        command=lambda: salvar_livro(campo_titulo, campo_autor, campo_ano, campo_quantidade)
    )
    botao_salvar.pack(pady=15)

# TELA CADASTRAR LEITOR
def cadastrar_leitor():
    tela = tk.Toplevel(janela)
    tela.title("Cadastro de Leitor")
    tela.geometry("450x400")
    tela.resizable(False, False)

    tk.Label(
        tela,
        text = "CADASTRAR LEITOR",
        font = ("Arial", 16, "bold"),
    ).pack(pady=20)

    formulario = tk.Frame(tela)
    formulario.pack(padx=30, pady=10)

    tk.Label(formulario, text="Nome:").grid(row=0, column=0, sticky="w", pady=8)
    campo_nome = tk.Entry(formulario, width=35)
    campo_nome.grid(row=0, column=1, pady=8)

    tk.Label(formulario, text="CPF:").grid(row=1, column=0, pady=8)
    campo_cpf = tk.Entry(formulario, width=35)
    campo_cpf.grid(row=1, column=1, pady=8)

    tk.Label(formulario, text="Telefone:").grid(row=2, column=0, pady=8)
    campo_telefone = tk.Entry(formulario, width=35)
    campo_telefone.grid(row=2, column=1, pady=8)

    tk.Label(formulario, text="E-mail:").grid(row=3, column=0, pady=8)
    campo_email = tk.Entry(formulario, width=35)
    campo_email.grid(row=3, column=1, pady=8)

    tk.Button(
        tela,
        text="Salvar",
        width=20,
        height=2,
        command=lambda: salvar_leitor(campo_nome, campo_cpf, campo_telefone, campo_email)
    ).pack(pady=15)

# TELA LISTAR LIVROS
def listar_livros():
    tela = tk.Toplevel(janela)
    tela.title("Lista de livros")
    tela.geometry("850x500")

    colunas = ("id", "titulo", "autor", "ano", "quantidade")

    tabela = ttk.Treeview(
        tela,
        columns=colunas,
        show="headings",
        selectmode="browse"
    )

    for coluna, texto in zip(
        colunas,
        ("ID", "Título", "Autor", "Ano", "Quantidade")
    ):
        tabela.heading(coluna, text=texto)

    tabela.column("id", width=50)
    tabela.column("titulo", width=200)
    tabela.column("autor", width=170)
    tabela.column("ano", width=70)
    tabela.column("quantidade", width=90)

    def carregar_livros():
        for item in tabela.get_children():
            tabela.delete(item)

        conexao = conectar()

        if conexao is None:
            messagebox.showerror("Erro", "Não foi possível conectar-se ao banco de dados.")
            return

        cursor = None

        try:
            cursor = conexao.cursor()
            cursor.execute('''
                SELECT id, titulo, autor, ano, quantidade
                FROM livros
                ORDER BY titulo
            ''')

            for livro in cursor.fetchall():
                tabela.insert("", tk.END, values=livro)

        except mysql.connector.Error:
            messagebox.showerror("Erro", "Não foi possível carregar os livros.")

        finally:
            if cursor is not None:
                cursor.close()
            conexao.close()

    def excluir_livro():
        selecionado = tabela.selection()

        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um livro para excluir.")
            return

        valores = tabela.item(selecionado[0], "values")
        id_livro = int(valores[0])

        confirmar = messagebox.askyesno(
            "Confirmar exclusão",
            f"Deseja excluir o livro '{valores[1]}'?"
        )

        if not confirmar:
            return

        conexao = conectar()

        if conexao is None:
            messagebox.showerror("Erro", "Não foi possível conectar-se ao banco de dados.")
            return

        cursor = None

        try:
            cursor = conexao.cursor()

            cursor.execute('''SELECT COUNT(*) FROM emprestimos WHERE livro_id = %s''',
                           (id_livro,))

            quantidade_emprestimos = cursor.fetchone()[0]

            if quantidade_emprestimos > 0:
                messagebox.showwarning(
                    "Exclusão não permitida",
                    "Este livro possui histórico de empréstimos e não pode ser excluído."
                )
                return

            cursor.execute(
                "DELETE FROM livros WHERE id = %s",
                (id_livro,)
            )

            conexao.commit()

            messagebox.showinfo("Ok", "Livro excluído com sucesso.")

            carregar_livros()

        except mysql.connector.Error:
            conexao.rollback()
            messagebox.showerror("Erro", "Não foi possível excluir o livro.")

        finally:
            if cursor is not None:
                cursor.close()
            conexao.close()

    def editar_livro():
        selecionado = tabela.selection()

        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um livro para editar.")
            return

        valores = tabela.item(selecionado[0], "values")
        id_livro = int(valores[0])

        editor = tk.Toplevel(tela)
        editor.title("Editar livro")
        editor.geometry("420x400")
        editor.resizable(False, False)

        tk.Label(
            editor,
            text="EDITAR LIVRO",
            font=("Arial", 15, "bold")
        ).pack(pady=15)

        formulario = tk.Frame(editor)
        formulario.pack(pady=5)

        campos = [
            ("Título:", valores[1]),
            ("Autor:", valores[2]),
            ("Ano:", valores[3]),
            ("Quantidade:", valores[4]),
        ]

        entradas = {}

        for linha, (rotulo, valor) in enumerate(campos):
            tk.Label(
                formulario,
                text=rotulo
            ).grid(row=linha, column=0, padx=8, pady=7, sticky="e")

            entrada = tk.Entry(formulario, width=30)
            entrada.grid(row=linha, column=1, padx=8, pady=7)
            entrada.insert(0, str(valor))
            entradas[rotulo] = entrada

        def salvar_edicao():
            titulo = entradas["Título:"].get().strip()
            autor = entradas["Autor:"].get().strip()
            ano_texto = entradas["Ano:"].get().strip()
            quantidade_texto = entradas["Quantidade:"].get().strip()

            if not titulo or not autor or not ano_texto or not quantidade_texto:
                messagebox.showwarning("Aviso", "Preencha todos os campos.")
                return

            if not ano_texto.isdigit() or int(ano_texto) <= 0:
                messagebox.showwarning("Aviso", "Informe um ano válido.")
                return

            if not quantidade_texto.isdigit():
                messagebox.showwarning("Aviso", "A quantidade deve ser um número inteiro.")
                return

            if int(quantidade_texto) < 0:
                messagebox.showwarning("Aviso", "A quantidade não pode ser negativa.")
                return

            conexao = conectar()

            if conexao is None:
                messagebox.showerror("Erro", "Não foi possível conectar-se ao banco de dados.")
                return

            cursor = None

            try:
                cursor = conexao.cursor()

                cursor.execute('''
                    SELECT COUNT(*)
                    FROM emprestimos
                    WHERE livro_id = %s AND data_devolucao IS NULL
                ''', (id_livro,))

                emprestimos_abertos = cursor.fetchone()[0]

                if int(quantidade_texto) < emprestimos_abertos:
                    messagebox.showwarning(
                        "Aviso",
                        "A quantidade disponível não pode ser menor que o número de empréstimos em aberto."
                    )
                    return

                cursor.execute(
                    '''
                    UPDATE livros 
                    SET titulo = %s, autor = %s, ano = %s, quantidade = %s
                    WHERE id = %s
                    ''',
                    (
                        titulo,
                        autor,
                        int(ano_texto),
                        int(quantidade_texto),
                        id_livro
                    )
                )

                conexao.commit()

                messagebox.showinfo("Ok", "Livro atualizado com sucesso.")
                editor.destroy()
                carregar_livros()

            except mysql.connector.Error:
                conexao.rollback()
                messagebox.showerror("Erro", "Não foi possível atualizar o livro.")

            finally:
                if cursor is not None:
                    cursor.close()
                conexao.close()

        tk.Button(
            editor,
            text="Salvar alterações",
            width=22,
            command=salvar_edicao
        ).pack(pady=15)

    barra = tk.Frame(tela)
    barra.pack(fill="x", padx=10, pady=10)

    tk.Button(
        barra,
        text="Atualizar",
        command=carregar_livros
    ).pack(side="left", padx=5)

    tk.Button(
        barra,
        text="Excluir livro",
        command=excluir_livro
    ).pack(side="left", padx=5)

    tk.Button(
        barra,
        text="Editar livro",
        command=editar_livro
    ).pack(side="left", padx=5)

    tabela.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=10
    )

    carregar_livros()

# TELA LISTAR LEITORES
def listar_leitores():
    tela = tk.Toplevel(janela)
    tela.title("Lista de leitores")
    tela.geometry("850x500")

    colunas = ("id", "nome", "cpf", "telefone", "email")

    tabela = ttk.Treeview(
        tela,
        columns=colunas,
        show="headings",
        selectmode="browse"
    )

    for coluna, texto in zip(
        colunas,
        ("ID", "Nome", "CPF", "Telefone", "E-mail")
    ):
        tabela.heading(coluna, text=texto)

    tabela.column("id", width=50)
    tabela.column("nome", width=180)
    tabela.column("cpf", width=120)
    tabela.column("telefone", width=130)
    tabela.column("email", width=250)

    def carregar_leitores():
        for item in tabela.get_children():
            tabela.delete(item)

        conexao = conectar()

        if conexao is None:
            messagebox.showerror("Erro", "Não foi possível conectar-se ao banco de dados.")
            return

        cursor = None

        try:
            cursor = conexao.cursor()
            cursor.execute('''
                SELECT id, nome, cpf, telefone, email
                FROM leitores
                ORDER BY nome
            ''')

            for usuario in cursor.fetchall():
                tabela.insert("", tk.END, values=usuario)

        except mysql.connector.Error:
            messagebox.showerror("Erro", "Não foi possível carregar os leitores.")

        finally:
            if cursor is not None:
                cursor.close()
            conexao.close()

    def excluir_leitor():
        selecionado = tabela.selection()

        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um usuário para excluir.")
            return

        valores = tabela.item(selecionado[0], "values")
        id_usuario = int(valores[0])

        if not messagebox.askyesno(
            "Confirmar exclusão",
            f"Deseja excluir o usuário '{valores[1]}'?"
        ):
            return

        conexao = conectar()

        if conexao is None:
            messagebox.showerror("Erro", "Não foi possível conectar-se ao banco de dados.")
            return

        cursor = None

        try:
            cursor = conexao.cursor()

            cursor.execute('''SELECT COUNT(*) FROM emprestimos WHERE leitor_id = %s''', (id_usuario,))

            if cursor.fetchone()[0] > 0:
                messagebox.showwarning(
                    "Exclusão não permitida",
                    "Este leitor possui histórico de empréstimos e não pode ser excluído."
                )
                return

            cursor.execute(
                '''DELETE FROM leitores WHERE id = %s''',
                (id_usuario,)
            )

            conexao.commit()

            messagebox.showinfo("Ok", "Leitor excluído com sucesso.")

            carregar_leitores()

        except mysql.connector.Error:
            conexao.rollback()
            messagebox.showerror("Erro","Não foi possível excluir o leitor."
            )

        finally:
            if cursor is not None:
                cursor.close()
            conexao.close()

    def editar_leitor():
        selecionado = tabela.selection()

        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um leitor para editar.")
            return

        valores = tabela.item(selecionado[0], "values")
        id_usuario = int(valores[0])

        editor = tk.Toplevel(tela)
        editor.title("Editar leitor")
        editor.geometry("420x350")
        editor.resizable(False, False)

        tk.Label(
            editor,
            text="EDITAR LEITOR",
            font=("Arial", 15, "bold")
        ).pack(pady=15)

        formulario = tk.Frame(editor)
        formulario.pack(pady=5)

        campos = [
            ("Nome:", valores[1]),
            ("CPF:", valores[2]),
            ("Telefone:", valores[3]),
            ("E-mail:", valores[4])
        ]

        entradas = {}

        for linha, (rotulo, valor) in enumerate(campos):
            tk.Label(
                formulario,
                text=rotulo
            ).grid(row=linha, column=0, padx=8, pady=7, sticky="e")

            entrada = tk.Entry(formulario, width=30)
            entrada.grid(row=linha, column=1, padx=8, pady=7)
            entrada.insert(0, str(valor))
            entradas[rotulo] = entrada

        def salvar_edicao():
            nome = entradas["Nome:"].get().strip()
            cpf = entradas["CPF:"].get().strip()
            cpf = cpf.replace(".", "").replace("-", "").replace(" ", "")
            telefone = entradas["Telefone:"].get().strip()
            email = entradas["E-mail:"].get().strip()

            if not nome or not cpf or not telefone or not email:
                messagebox.showwarning("Aviso", "Preencha todos os campos.")
                return

            if not cpf.isdigit() or len(cpf) != 11:
                messagebox.showwarning("Aviso", "O CPF deve conter 11 dígitos.")
                return

            partes_email = email.split("@")

            if (
                len(partes_email) != 2
                or not partes_email[0]
                or "." not in partes_email[1]
            ):
                messagebox.showwarning("Aviso", "Informe um e-mail válido.")
                return

            conexao = conectar()

            if conexao is None:
                messagebox.showerror("Erro", "Não foi possível conectar-se ao banco de dados.")
                return

            cursor = None

            try:
                cursor = conexao.cursor()

                cursor.execute('''SELECT id FROM leitores WHERE cpf = %s AND id <> %s''',
                               (cpf, id_usuario)
                               )

                if cursor.fetchone() is not None:
                    messagebox.showwarning("Aviso", "Já existe outro leitor com esse CPF.")
                    return

                cursor.execute('''
                    UPDATE leitores
                    SET nome = %s, cpf = %s, telefone = %s, email = %s
                    WHERE id = %s
                ''', (nome, cpf, telefone, email, id_usuario))

                conexao.commit()

                messagebox.showinfo("Ok","Leitor atualizado com sucesso.")
                editor.destroy()
                carregar_leitores()

            except mysql.connector.Error:
                conexao.rollback()
                messagebox.showerror("Erro", "Não foi possível atualizar o leitor.")

            finally:
                if cursor is not None:
                    cursor.close()
                conexao.close()

        tk.Button(
            editor,
            text="Salvar alterações",
            width=22,
            command=salvar_edicao
        ).pack(pady=15)

    barra = tk.Frame(tela)
    barra.pack(fill="x", padx=10, pady=10)

    tk.Button(
        barra,
        text="Atualizar",
        command=carregar_leitores
    ).pack(side="left", padx=5)

    tk.Button(
        barra,
        text="Editar leitor",
        command=editar_leitor
    ).pack(side="left", padx=5)

    tk.Button(
        barra,
        text="Excluir leitor",
        command=excluir_leitor
    ).pack(side="left", padx=5)

    tabela.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=10
    )

    carregar_leitores()

# TELA LISTAR EMPRÉSTIMOS
def listar_emprestimos():
    tela = tk.Toplevel(janela)
    tela.title("Lista de empréstimos")
    tela.geometry("1000x450")

    colunas = ("id", "leitor", "livro", "data_emprestimo", "data_devolucao", "status")

    tabela = ttk.Treeview(
        tela,
        columns=colunas,
        show="headings"
    )

    tabela.heading("id", text="ID")
    tabela.heading("leitor", text="Leitor")
    tabela.heading("livro", text="Livro")
    tabela.heading("data_emprestimo", text="Data Empréstimo")
    tabela.heading("data_devolucao", text="Data Devolução")
    tabela.heading("status", text="Situação")

    tabela.column("id", width=50, anchor="center")
    tabela.column("leitor", width=180, anchor="center")
    tabela.column("livro", width=220, anchor="center")
    tabela.column("data_emprestimo", width=140, anchor="center")
    tabela.column("data_devolucao", width=140, anchor="center")
    tabela.column("status", width=120, anchor="center")

    def carregar_emprestimos():
        for item in tabela.get_children():
            tabela.delete(item)

        conexao = conectar()

        if conexao is None:
            messagebox.showerror("Erro", "Não foi possível conectar-se ao banco de dados.")
            return

        cursor = None

        try:
            cursor = conexao.cursor()

            cursor.execute('''
                SELECT emprestimos.id, leitores.nome, livros.titulo, emprestimos.data_emprestimo, emprestimos.data_devolucao
                FROM emprestimos
                INNER JOIN leitores ON emprestimos.leitor_id = leitores.id
                INNER JOIN livros ON emprestimos.livro_id = livros.id
                ORDER BY emprestimos.id DESC
            ''')

            emprestimos = cursor.fetchall()

            for emprestimo in emprestimos:
                data_devolucao = emprestimo[4]

                if data_devolucao is None:
                    data_devolucao = "-"
                    status = "Em aberto"
                else:
                    status = "Devolvido"

                tabela.insert(
                    "",
                    tk.END,
                    values=(
                        emprestimo[0],
                        emprestimo[1],
                        emprestimo[2],
                        emprestimo[3],
                        data_devolucao,
                        status
                    )
                )

        except mysql.connector.Error:
            messagebox.showerror("Erro", "Não foi possível carregar os empréstimos.")

        finally:
            if cursor is not None:
                cursor.close()
            conexao.close()

    barra = tk.Frame(tela)
    barra.pack(fill="x", padx=10, pady=10)

    tk.Button(
        barra,
        text="Atualizar",
        command=carregar_emprestimos
    ).pack(side="left")

    tabela.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=10
    )

    carregar_emprestimos()

# TELA EMPRESTAR LIVRO
def emprestar_livro():
    tela = tk.Toplevel(janela)
    tela.title("Emprestar Livro")
    tela.geometry("500x320")
    tela.resizable(False, False)

    tk.Label(
        tela,
        text="REGISTRAR EMPRÉSTIMO",
        font=("Arial", 16, "bold")
    ).pack(pady=20)

    formulario = tk.Frame(tela)
    formulario.pack(pady=10)

    tk.Label(formulario, text="Leitor:").grid(row=0, column=0, padx=8, pady=10, sticky="e")
    campo_leitor = ttk.Combobox(formulario, width=32, state="readonly")
    campo_leitor.grid(row=0, column=1, padx=8, pady=10)

    tk.Label(formulario, text="Livro:").grid(row=1, column=0, padx=8, pady=10, sticky="e")
    campo_livro = ttk.Combobox(formulario, width=32, state="readonly")
    campo_livro.grid(row=1, column=1, padx=8, pady=10)

    conexao = conectar()

    if conexao is None:
        messagebox.showerror("Erro","Não foi possível conectar-se ao banco de dados.")
        tela.destroy()
        return

    cursor = None

    try:
        cursor = conexao.cursor()
        cursor.execute('''SELECT id, nome FROM leitores ORDER BY nome''')
        leitores = cursor.fetchall()

        cursor.execute('''SELECT id, titulo FROM livros WHERE quantidade > 0 ORDER BY titulo''')
        livros = cursor.fetchall()

        campo_leitor["values"] = [
            f"{leitor[0]} - {leitor[1]}"
            for leitor in leitores
        ]

        campo_livro["values"] = [
            f"{livro[0]} - {livro[1]}"
            for livro in livros
        ]

    except mysql.connector.Error:
        messagebox.showerror("Erro", "Não foi possível carregar usuários e livros.")
        tela.destroy()
        return

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

    campo_id_leitor = tk.Entry(tela)
    campo_id_livro = tk.Entry(tela)

    def executar_emprestimo():
        leitor_selecionado = campo_leitor.get()
        livro_selecionado = campo_livro.get()

        if not leitor_selecionado or not livro_selecionado:
            messagebox.showwarning("Aviso", "Selecione um leitor e um livro.")
            return

        campo_id_leitor.delete(0, tk.END)
        campo_id_leitor.insert(0, leitor_selecionado.split(" - ", 1)[0])
        campo_id_livro.delete(0, tk.END)
        campo_id_livro.insert(0, livro_selecionado.split(" - ", 1)[0])

        registrar_emprestimo(campo_id_leitor, campo_id_livro)

    tk.Button(
        tela,
        text="Confirmar",
        width=25,
        command=executar_emprestimo
    ).pack(pady=15)

# TELA DEVOLVER LIVRO
def devolver_livro():
    tela = tk.Toplevel(janela)
    tela.title("Devolver Livro")
    tela.geometry("550x300")
    tela.resizable(False, False)

    tk.Label(
        tela,
        text="REGISTRAR DEVOLUÇÃO",
        font=("Arial", 16, "bold")
    ).pack(pady=20)

    tk.Label(
        tela,
        text="Selecione o empréstimo:"
    ).pack(pady=5)

    campo_emprestimo = ttk.Combobox(
        tela,
        width=55,
        state="readonly"
    )
    campo_emprestimo.pack(pady=10)

    conexao = conectar()

    if conexao is None:
        messagebox.showerror("Erro", "Não foi possível conectar-se ao banco de dados.")
        tela.destroy()
        return

    cursor = None
    emprestimos = []

    try:
        cursor = conexao.cursor()
        cursor.execute('''
            SELECT emprestimos.id, leitores.nome, livros.titulo, emprestimos.data_emprestimo
            FROM emprestimos
            INNER JOIN leitores ON emprestimos.leitor_id = leitores.id
            INNER JOIN livros ON emprestimos.livro_id = livros.id
            WHERE emprestimos.data_devolucao IS NULL
            ORDER BY leitores.nome, livros.titulo
        ''')

        emprestimos = cursor.fetchall()

        campo_emprestimo["values"] = [
            f"ID {item[0]} - {item[1]} - {item[2]} - {item[3]}"
            for item in emprestimos
        ]

    except mysql.connector.Error:
        messagebox.showerror("Erro", "Não foi possível carregar os empréstimos.")
        tela.destroy()
        return

    finally:
        if cursor is not None:
            cursor.close()
        conexao.close()

    if not emprestimos:
        messagebox.showinfo("Devoluções", "Não existem empréstimos em aberto.")

    def confirmar_devolucao():
        selecionado = campo_emprestimo.current()

        if selecionado < 0:
            messagebox.showwarning("Aviso", "Selecione um empréstimo.")
            return

        id_emprestimo = emprestimos[selecionado][0]

        campo_id = tk.Entry(tela)
        campo_id.insert(0, str(id_emprestimo))

        registrar_devolucao(campo_id)

        campo_id.destroy()

        if selecionado < len(emprestimos):
            tela.destroy()

    tk.Button(
        tela,
        text="Confirmar",
        width=25,
        command=confirmar_devolucao
    ).pack(pady=15)

# TELA MENU PRINCIPAL
janela = tk.Tk()
janela.title("Sistema de Gerenciamento Bibliotecário")
janela.geometry("750x600")
janela.resizable(False, False)
janela.configure(bg="#FFFAFA")

# ESTILOS
estilo = ttk.Style()
estilo.configure(
    'Menu.TButton',
    font=("Arial", 11, "bold"),
    padding=(12, 10),
    foreground="#000000",
    background="#000000"
)

estilo.map(
    'Menu.TButton',
    background=[
        ("active", "#000000"),
        ("pressed", "#000000")
    ],
    foreground=[
        ("active", "#000000")
    ]
)
estilo.theme_use("clam")

estilo.configure(
    "TButton",
    font=("Arial", 11),
    padding=12
)

estilo.configure(
    "TLabel",
    font=("Arial", 11)
)

estilo.configure(
    "Treeview",
    font=("Arial", 10),
    rowheight=28
)

estilo.configure(
    "Treeview.Heading",
    font=("Arial", 10, "bold")
)

titulo = tk.Label(
    janela,
    text = "SISTEMA DE GERENCIAMENTO BIBLIOTECÁRIO",
    font = ("Arial", 20, "bold"),
    bg="#FFFAFA",
    fg="#000000"
)
titulo.pack(pady=40)

subtitulo = tk.Label(
    janela,
    text = "Escolha uma opção:",
    font = ("Arial", 15),
    bg="#FFFAFA",
    fg="#000000"
)
subtitulo.pack(pady=5)

quadro = tk.Frame(janela)
quadro.pack(pady=20)
quadro.columnconfigure(0, weight=1, uniform="botoes")
quadro.columnconfigure(1, weight=1, uniform="botoes")

# BOTÕES DO MENU PRINCIPAL
botao_cadastrar_livro = ttk.Button(
    quadro, text="Cadastrar Livro", style="Menu.TButton", command=cadastrar_livro
)
botao_cadastrar_livro.grid(row = 0, column = 0, padx = 10, pady = 10, sticky="ew")

botao_cadastrar_usuario = ttk.Button(
    quadro, text="Cadastrar Leitor", style="Menu.TButton", command=cadastrar_leitor
)
botao_cadastrar_usuario.grid(row = 0, column = 1, padx = 10, pady = 10, sticky="ew")

botao_listar_livros = ttk.Button(
    quadro, text="Listar Livros", style="Menu.TButton", command=listar_livros
)
botao_listar_livros.grid(row = 1, column = 0, padx = 10, pady = 10, sticky="ew")

botao_listar_leitores = ttk.Button(
    quadro, text="Listar Leitores", style="Menu.TButton", command=listar_leitores
)
botao_listar_leitores.grid(row = 1, column = 1, padx = 10, pady = 10, sticky="ew")

botao_listar_emprestimos = ttk.Button(
    quadro, text="Listar Empréstimos", style="Menu.TButton", command=listar_emprestimos
)
botao_listar_emprestimos.grid(row = 2, column = 0, padx = 10, pady = 10, sticky="ew")

botao_emprestar = ttk.Button(
    quadro, text="Emprestar Livro", style="Menu.TButton", command=emprestar_livro
)
botao_emprestar.grid(row = 3, column = 0, padx = 10, pady = 10, sticky="ew")

botao_devolver_livro = ttk.Button(
    quadro, text="Devolver Livro", style="Menu.TButton", command=devolver_livro
)
botao_devolver_livro.grid(row = 3, column = 1, padx = 10, pady = 10, sticky="ew")

janela.mainloop()