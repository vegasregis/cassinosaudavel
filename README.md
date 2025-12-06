import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import random
import math
import webbrowser

# ==============================
# ARQUIVOS DE IMAGEM
# ==============================

ARQUIVO_DRAGAO = "dragao_background.png"

ARQUIVOS_SIMBOLOS = {
    "dragao": "sym_dragao.png",
    "fogo": "sym_fogo.png",
    "orbe": "sym_orbe.png",
    "moeda": "sym_moeda.png",
    "lotos": "sym_lotos.png",
    "estrela": "sym_estrela.png",
}

# ==============================
# FUNÇÕES TALEBIANAS
# ==============================

def gerar_retorno_volatil(media: float, desvio: float) -> dict:
    r = random.random()

    if r < 0.60:
        retorno = random.gauss(media * 0.5, desvio * 0.5)
    elif r < 0.90:
        retorno = random.gauss(media * 1.5, desvio * 0.8)
    else:
        retorno = random.gauss(media * 5, desvio * 2)

    if retorno > media + 3 * desvio:
        tipo = "cauda_extrema_positiva"
    elif retorno > media + 2 * desvio:
        tipo = "cauda_positiva"
    elif retorno < media - 2 * desvio:
        tipo = "cauda_negativa"
    else:
        tipo = "normal"

    return {"retorno": retorno, "tipo": tipo}


def calcular_sharpe_ratio(retornos, taxa_livre_risco: float = 0.01) -> float:
    if not retornos or len(retornos) < 2:
        return 0.0

    retorno_medio = sum(retornos) / len(retornos)
    variancia = sum((r - retorno_medio) ** 2 for r in retornos) / (len(retornos) - 1)
    desvio_padrao = math.sqrt(variancia)

    if desvio_padrao == 0:
        return 0.0

    return (retorno_medio - taxa_livre_risco) / desvio_padrao


def calcular_drawdown_maximo(valores):
    if not valores:
        return 0.0

    pico = valores[0]
    max_dd = 0.0

    for valor in valores:
        if valor > pico:
            pico = valor
        dd = (pico - valor) / pico if pico > 0 else 0
        if dd > max_dd:
            max_dd = dd

    return max_dd


def simular_tesouraria_taleb(
    capital_inicial=50000.0,
    retorno_mensal_rf_min=0.008,
    retorno_mensal_rf_max=0.012,
    retorno_volatil_media=0.05,
    retorno_volatil_desvio=0.20,
    aporte_mensal=1000.0,
    periodos=24,
    percentual_seguro=0.90,
    percentual_volatil=0.10,
):
    capital_seguro = capital_inicial * percentual_seguro
    capital_volatil = capital_inicial * percentual_volatil
    jackpot_simulado = 0.0

    historico_total = [capital_seguro + capital_volatil + jackpot_simulado]
    retornos_mensais = []
    eventos_cauda = []

    for mes in range(1, periodos + 1):
        retorno_rf = random.uniform(retorno_mensal_rf_min, retorno_mensal_rf_max)
        capital_seguro *= 1 + retorno_rf

        capital_volatil += aporte_mensal

        resultado_volatil = gerar_retorno_volatil(
            retorno_volatil_media, retorno_volatil_desvio
        )
        retorno_vol = resultado_volatil["retorno"]
        tipo_evento = resultado_volatil["tipo"]

        capital_antes = capital_volatil
        capital_volatil *= 1 + retorno_vol
        capital_volatil = max(capital_volatil, 0)

        ganho_perdido = capital_volatil - capital_antes

        contribuicao_jackpot = 0
        if ganho_perdido > 0:
            contribuicao_jackpot = ganho_perdido * 0.20
            jackpot_simulado += contribuicao_jackpot
            capital_volatil -= contribuicao_jackpot

        if tipo_evento != "normal":
            eventos_cauda.append(
                {
                    "mes": mes,
                    "tipo": tipo_evento,
                    "retorno": round(retorno_vol * 100, 2),
                    "variacao": round(ganho_perdido, 2),
                    "contribuicao_jackpot": round(contribuicao_jackpot, 2),
                }
            )

        patrimonio_total = capital_seguro + capital_volatil + jackpot_simulado
        retorno_mensal_patrimonio = (patrimonio_total - historico_total[-1]) / (
            historico_total[-1]
        )
        historico_total.append(patrimonio_total)
        retornos_mensais.append(retorno_mensal_patrimonio)

    patrimonio_final = historico_total[-1]
    patrimonio_inicial = historico_total[0]
    retorno_total = patrimonio_final - patrimonio_inicial
    crescimento_percentual = (retorno_total / patrimonio_inicial) * 100

    drawdown_maximo = calcular_drawdown_maximo(historico_total)
    sharpe_ratio = calcular_sharpe_ratio(retornos_mensais)
    jackpot_acumulado = jackpot_simulado

    return {
        "capital_seguro_final": capital_seguro,
        "capital_volatil_final": capital_volatil,
        "jackpot_final": jackpot_acumulado,
        "retorno_total": retorno_total,
        "crescimento_percentual": crescimento_percentual,
        "drawdown_maximo": drawdown_maximo,
        "sharpe_ratio": sharpe_ratio,
        "eventos_cauda": eventos_cauda,
    }


# ==============================
# APP TKINTER – CASSINO SAUDÁVEL
# ==============================

class CassinoSaudavelApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cassino Saudável – Fortune Dragon Balance")
        self.root.geometry("420x780")
        self.root.config(bg="#8A0000")

        # cor base dos slots
        self.slot_bg = "#8A0000"

        # ECONOMIA
        self.saldo_dinheiro = 0.0
        self.cofre_seguro = 0.0
        self.cofre_dragao = 0.0
        self.jackpot = 10_000.0
        self.creditos = 500
        self.aposta = 10
        self.taxa_conversao = 1.0

        # controle de animação
        self.spin_em_andamento = False

        # Símbolos do slot
        self.symbols = ["dragao", "fogo", "orbe", "moeda", "lotos", "estrela"]
        self.weights = [3, 7, 10, 15, 20, 30]
        # PAYTABLE AJUSTADA PARA ~96% RTP (base game)
        self.paytable = {
            "dragao": 28,
            "fogo": 13,
            "orbe": 10,
            "moeda": 5,
            "lotos": 4,
            "estrela": 2,
        }

        # Modo especial
        self.equilibrios_para_especial = 3
        self.multiplicador_especial = 2
        self.em_modo_especial = False
        self.giros_vencedores = 0

        # CARREGAR IMAGENS
        self.symbol_images = {}
        for simbolo, arquivo in ARQUIVOS_SIMBOLOS.items():
            try:
                img = Image.open(arquivo).resize((60, 60), Image.LANCZOS)
                self.symbol_images[simbolo] = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Erro ao carregar {arquivo}: {e}")
                self.symbol_images[simbolo] = None

        # TOPO
        self.top_canvas = tk.Canvas(
            root, width=420, height=150, bg="#8A0000", highlightthickness=0
        )
        self.top_canvas.pack()
        self._carregar_background()

        tk.Label(
            root,
            text="Cassino Saudável – Slots 3x3",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#8A0000",
        ).pack(pady=4)

        # PAINEL DE CAIXAS
        self._criar_painel_caixas()
        self._atualizar_painel_caixas()

        # ÁREA DE DEPÓSITO
        self._criar_area_deposito()

        # ÁREA DE SAQUE
        self._criar_area_saque()

        # INFO
        self.info_label = tk.Label(
            root,
            text=self._texto_info(),
            font=("Arial", 6),
            fg="white",
            bg="#8A0000",
            wraplength=380,
            justify="center",
        )
        self.info_label.pack(pady=6)

        # SLOTS
        self.frame_slots = tk.Frame(root, bg="#8A0000")
        self.frame_slots.pack(pady=10)

        self.slots = []
        for i in range(3):
            linha = []
            for j in range(3):
                lbl = tk.Label(self.frame_slots, bg=self.slot_bg)
                lbl.grid(row=i, column=j, padx=8, pady=6)
                linha.append(lbl)
            self.slots.append(linha)

        # RESULTADO
        self.result_label = tk.Label(
            root,
            text="Clique em INICIAR FLUXO.",
            font=("Arial", 6),
            fg="white",
            bg="#8A0000",
            wraplength=280,
            justify="center",
        )
        self.result_label.pack(pady=6)

        # BOTÕES (sempre no final)
        self.frame_botoes = tk.Frame(root, bg="#8A0000")
        self.frame_botoes.pack(pady=6)

        self.btn_spin = tk.Button(
            self.frame_botoes,
            text="INICIAR FLUXO",
            font=("Arial", 6, "bold"),
            bg="gold",
            fg="black",
            command=self.spin,
        )
        self.btn_spin.pack(pady=4)

        self.btn_special = tk.Button(
            self.frame_botoes,
            text="MODO ESPECIAL (8 GIROS)",
            font=("Arial", 6, "bold"),
            bg="#FFD700",
            fg="black",
            state="disabled",
            command=self.iniciar_modo_especial,
        )
        self.btn_special.pack(pady=2)

        self.btn_simular_tesouraria = tk.Button(
            self.frame_botoes,
            text="📊 Simular Tesouraria Taleb",
            font=("Arial", 4, "bold"),
            bg="#444",
            fg="white",
            command=self.simular_tesouraria,
        )
        self.btn_simular_tesouraria.pack(pady=2)

        self.btn_atualizar_dia = tk.Button(
            self.frame_botoes,
            text="🔁 Atualizar 1 dia (juros + volátil)",
            font=("Arial", 8, "bold"),
            bg="#555",
            fg="white",
            command=self.atualizar_um_dia,
        )
        self.btn_atualizar_dia.pack(pady=2)

        self.btn_link = tk.Button(
            self.frame_botoes,
            text="🔗 Código do Caos",
            font=("Arial", 2, "bold"),
            bg="#444",
            fg="white",
            command=self.abrir_link,
        )
        self.btn_link.pack(pady=2)

    # ======================
    # PAINEL / ECONOMIA
    # ======================

    def _criar_painel_caixas(self):
        painel = tk.Frame(self.root, bg="#8A0000")
        painel.pack(pady=4)

        def criar_box(pai, titulo):
            frame = tk.Frame(
                pai, bg="#5B0000", bd=1, relief="ridge", padx=6, pady=4
            )
            tk.Label(
                frame,
                text=titulo,
                font=("Arial", 7, "bold"),
                fg="white",
                bg="#5B0000",
            ).pack()
            lbl_valor = tk.Label(
                frame,
                text="R$ 0,00",
                font=("Arial", 7, "bold"),
                fg="gold",
                bg="#5B0000",
            )
            lbl_valor.pack()
            return frame, lbl_valor

        self.box_saldo, self.lbl_saldo = criar_box(painel, "💰 Saldo")
        self.box_cofre_seguro, self.lbl_cofre_seguro = criar_box(
            painel, "🏦 Cofre Seguro"
        )
        self.box_cofre_dragao, self.lbl_cofre_dragao = criar_box(
            painel, "🐉 Cofre do Dragão"
        )
        self.box_jackpot, self.lbl_jackpot = criar_box(painel, "🎰 Jackpot")
        self.box_creditos, self.lbl_creditos = criar_box(painel, "🎟 Créditos")

        self.box_saldo.grid(row=0, column=0, padx=3)
        self.box_cofre_seguro.grid(row=0, column=1, padx=3)
        self.box_cofre_dragao.grid(row=0, column=2, padx=3)
        self.box_jackpot.grid(row=0, column=3, padx=3)
        self.box_creditos.grid(row=0, column=4, padx=3)

    def _atualizar_painel_caixas(self):
        def fmt(valor):
            return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace(
                "X", "."
            )

        self.lbl_saldo.config(text=fmt(self.saldo_dinheiro))
        self.lbl_cofre_seguro.config(text=fmt(self.cofre_seguro))
        self.lbl_cofre_dragao.config(text=fmt(self.cofre_dragao))
        self.lbl_jackpot.config(text=fmt(self.jackpot))
        self.lbl_creditos.config(text=str(self.creditos))

    def gastar_creditos(self, valor):
        self.creditos -= valor
        self._atualizar_painel_caixas()

    def ganhar_creditos(self, valor):
        self.creditos += valor
        self._atualizar_painel_caixas()

    # ======================
    # DEPÓSITO
    # ======================

    def _criar_area_deposito(self):
        frame = tk.Frame(self.root, bg="#8A0000")
        frame.pack(pady=4)

        tk.Label(
            frame,
            text="Valor (R$):",
            font=("Arial", 9),
            fg="white",
            bg="#8A0000",
        ).grid(row=0, column=0, padx=3)

        self.entry_deposito = tk.Entry(frame, width=10)
        self.entry_deposito.grid(row=0, column=1, padx=3)

        btn_dep = tk.Button(
            frame,
            text="Depositar",
            font=("Arial", 9, "bold"),
            bg="#228B22",
            fg="white",
            command=self.depositar,
        )
        btn_dep.grid(row=0, column=2, padx=3)

        btn_conv = tk.Button(
            frame,
            text="Converter em Créditos",
            font=("Arial", 9, "bold"),
            bg="#1E90FF",
            fg="white",
            command=self.converter_para_creditos,
        )
        btn_conv.grid(row=0, column=3, padx=3)

    def _ler_valor_entry(self):
        texto = self.entry_deposito.get().strip().replace(",", ".")
        if not texto:
            return None
        try:
            return float(texto)
        except ValueError:
            return None

    def depositar(self):
        valor = self._ler_valor_entry()
        if valor is None or valor <= 0:
            self.result_label.config(
                text="Informe um valor válido para depósito.",
                fg="red",
            )
            return

        self.saldo_dinheiro += valor
        self.cofre_seguro += valor * 0.90
        self.cofre_dragao += valor * 0.10

        self._atualizar_painel_caixas()
        self.entry_deposito.delete(0, tk.END)

        self.result_label.config(
            text=f"Depósito de R$ {valor:.2f} realizado (90% seguro / 10% dragão).",
            fg="gold",
        )

    def converter_para_creditos(self):
        valor = self._ler_valor_entry()
        if valor is None:
            valor = self.saldo_dinheiro

        if valor <= 0:
            self.result_label.config(text="Nada a converter.", fg="white")
            return

        if valor > self.saldo_dinheiro:
            self.result_label.config(
                text="Saldo insuficiente para converter esse valor.",
                fg="red",
            )
            return

        self.saldo_dinheiro -= valor
        creditos_gerados = int(valor * self.taxa_conversao)
        self.creditos += creditos_gerados

        self._atualizar_painel_caixas()
        self.entry_deposito.delete(0, tk.END)

        self.result_label.config(
            text=f"Convertidos R$ {valor:.2f} em {creditos_gerados} créditos.",
            fg="gold",
        )

    # ======================
    # SAQUE
    # ======================

    def _criar_area_saque(self):
        frame = tk.Frame(self.root, bg="#8A0000")
        frame.pack(pady=4)

        tk.Label(
            frame,
            text="Valor (R$) para saque:",
            font=("Arial", 8),
            fg="white",
            bg="#8A0000",
        ).grid(row=0, column=0, padx=3)

        self.entry_saque = tk.Entry(frame, width=10)
        self.entry_saque.grid(row=0, column=1, padx=3)

        btn_saque_seguro = tk.Button(
            frame,
            text="Sacar Cofre Seguro",
            font=("Arial", 7, "bold"),
            bg="#8B4513",
            fg="white",
            command=self.sacar_cofre_seguro,
        )
        btn_saque_seguro.grid(row=0, column=2, padx=3)

        btn_saque_dragao = tk.Button(
            frame,
            text="Sacar Cofre Dragão",
            font=("Arial", 7, "bold"),
            bg="#A52A2A",
            fg="white",
            command=self.sacar_cofre_dragao,
        )
        btn_saque_dragao.grid(row=0, column=3, padx=3)

        btn_saque_saldo = tk.Button(
            frame,
            text="Sacar Saldo",
            font=("Arial", 7, "bold"),
            bg="#2F4F4F",
            fg="white",
            command=self.sacar_saldo,
        )
        btn_saque_saldo.grid(row=1, column=0, columnspan=4, pady=3)

    def _ler_valor_saque(self):
        texto = self.entry_saque.get().strip().replace(",", ".")
        if not texto:
            return None
        try:
            return float(texto)
        except ValueError:
            return None

    def sacar_cofre_seguro(self):
        valor = self._ler_valor_saque()
        if valor is None or valor <= 0:
            self.result_label.config(text="Informe um valor válido para saque.", fg="red")
            return
        if valor > self.cofre_seguro:
            self.result_label.config(
                text="Valor maior que o disponível no Cofre Seguro.", fg="red"
            )
            return

        self.cofre_seguro -= valor
        self.saldo_dinheiro = 0.0
        self._atualizar_painel_caixas()
        self.entry_saque.delete(0, tk.END)

        self.result_label.config(
            text=f"Você sacou R$ {valor:.2f} do Cofre Seguro. Saldo interno zerado.",
            fg="gold",
        )

    def sacar_cofre_dragao(self):
        valor = self._ler_valor_saque()
        if valor is None or valor <= 0:
            self.result_label.config(text="Informe um valor válido para saque.", fg="red")
            return
        if valor > self.cofre_dragao:
            self.result_label.config(
                text="Valor maior que o disponível no Cofre do Dragão.", fg="red"
            )
            return

        self.cofre_dragao -= valor
        self.saldo_dinheiro = 0.0
        self._atualizar_painel_caixas()
        self.entry_saque.delete(0, tk.END)

        self.result_label.config(
            text=f"Você sacou R$ {valor:.2f} do Cofre do Dragão. Saldo interno zerado.",
            fg="gold",
        )

    def sacar_saldo(self):
        if self.saldo_dinheiro <= 0:
            self.result_label.config(text="Não há saldo para sacar.", fg="white")
            return
        valor = self.saldo_dinheiro
        self.saldo_dinheiro = 0.0
        self._atualizar_painel_caixas()
        self.result_label.config(
            text=f"Você sacou R$ {valor:.2f} do Saldo. Saldo interno zerado.",
            fg="gold",
        )

    # ======================
    # OUTROS
    # ======================

    def _texto_info(self):
        return (
            f"Modo Especial após {self.equilibrios_para_especial} giros vencedores.\n"
            f"No modo especial, cada linha vencedora paga x{self.multiplicador_especial}."
        )

    def abrir_link(self):
        webbrowser.open("https://google.com")

    def _carregar_background(self):
        try:
            img = Image.open(ARQUIVO_DRAGAO).resize((420, 250), Image.LANCZOS)
            self.bg = ImageTk.PhotoImage(img)
            self.top_canvas.create_image(0, 0, anchor="nw", image=self.bg)
        except Exception as e:
            print("Erro ao carregar imagem do dragão:", e)
            self.top_canvas.create_text(
                210, 75, text="Fortune Dragon", fill="white", font=("Arial", 18)
            )

    # ======================
    # SLOT – HELPERS
    # ======================

    def _set_slot_symbol(self, i, j, simbolo):
        img = self.symbol_images.get(simbolo)
        if img:
            self.slots[i][j].config(image=img, text="", bg=self.slot_bg, fg="white")
            self.slots[i][j].image = img
        else:
            self.slots[i][j].config(
                text=simbolo, fg="white", image="", bg=self.slot_bg
            )

    def _reset_highlight(self):
        for i in range(3):
            for j in range(3):
                self.slots[i][j].config(bg=self.slot_bg)

    def _gerar_grade_final(self):
        grade = []
        for i in range(3):
            linha = []
            for j in range(3):
                simbolo = random.choices(self.symbols, weights=self.weights)[0]
                linha.append(simbolo)
            grade.append(linha)
        return grade

    # ======================
    # CÁLCULO DE PRÊMIO / LINHAS
    # ======================

    def _calcular_premio(self, grade):
        premio = 0
        venceu = False
        linhas_vencedoras = []

        # HORIZONTAIS (3 linhas pagantes)
        for i in range(3):
            if grade[i][0] == grade[i][1] == grade[i][2]:
                venceu = True
                simbolo = grade[i][0]
                premio += self.aposta * self.paytable.get(simbolo, 0)
                linhas_vencedoras.append([(i, 0), (i, 1), (i, 2)])

        # NENHUMA VERTICAL PAGA (regra do jogo)
        # if grade[0][j] == grade[1][j] == grade[2][j]: # REMOVIDO

        # DIAGONAIS (2 linhas pagantes)
        if grade[0][0] == grade[1][1] == grade[2][2]:
            venceu = True
            simbolo = grade[0][0]
            premio += self.aposta * self.paytable.get(simbolo, 0)
            linhas_vencedoras.append([(0, 0), (1, 1), (2, 2)])

        if grade[0][2] == grade[1][1] == grade[2][0]:
            venceu = True
            simbolo = grade[0][2]
            premio += self.aposta * self.paytable.get(simbolo, 0)
            linhas_vencedoras.append([(0, 2), (1, 1), (2, 0)])

        return premio, venceu, linhas_vencedoras

    def _brilhar_linhas(self, linhas_vencedoras, ciclos=6, ligado=True):
        cor_on = "#FFD700"
        cor_off = self.slot_bg

        for indices in linhas_vencedoras:
            for (i, j) in indices:
                self.slots[i][j].config(bg=cor_on if ligado else cor_off)

        if ciclos > 0:
            self.root.after(
                150, self._brilhar_linhas, linhas_vencedoras, ciclos - 1, not ligado
            )
        else:
            for indices in linhas_vencedoras:
                for (i, j) in indices:
                    self.slots[i][j].config(bg=cor_on)

    def _finalizar_giro_normal(self, grade):
        premio, venceu, linhas_vencedoras = self._calcular_premio(grade)

        msg = ""
        if venceu:
            self.giros_vencedores += 1
            self.ganhar_creditos(premio)
            msg = f"✨ Você ganhou {premio} créditos!"

            # chance de ganhar um pouco do jackpot (aumenta RTP total)
            if self.jackpot > 0 and random.random() < 0.10:
                bonus = int(self.jackpot * random.uniform(0.01, 0.05))
                bonus = max(1, min(bonus, int(self.jackpot)))
                self.jackpot -= bonus
                self.ganhar_creditos(bonus)
                msg += f" 🎰 +{bonus} créditos de Jackpot!"

            self._brilhar_linhas(linhas_vencedoras)
        else:
            msg = "Nenhuma linha vencedora desta vez."

        if self.giros_vencedores >= self.equilibrios_para_especial:
            self.btn_special.config(state="normal")

        self._atualizar_painel_caixas()
        self.result_label.config(
            text=msg, fg="gold" if venceu else "white"
        )
        self.spin_em_andamento = False

    # ======================
    # GIRO NORMAL – COLUNA POR COLUNA
    # ======================

    def spin(self):
        if self.em_modo_especial or self.spin_em_andamento:
            return

        if self.creditos < self.aposta:
            self.result_label.config(
                text="Créditos insuficientes para girar. 💸", fg="red"
            )
            return

        self._reset_highlight()
        self.gastar_creditos(self.aposta)
        self.spin_em_andamento = True
        self.result_label.config(text="Girando...", fg="white")

        grade_final = self._gerar_grade_final()
        self._animar_giro_coluna(coluna=0, passos=12, grade_final=grade_final)

    def _animar_giro_coluna(self, coluna, passos, grade_final):
        if passos > 0:
            for i in range(3):
                for j in range(3):
                    if j < coluna:
                        simbolo = grade_final[i][j]
                    elif j == coluna:
                        simbolo = random.choices(self.symbols, weights=self.weights)[0]
                    else:
                        simbolo = random.choices(self.symbols, weights=self.weights)[0]
                    self._set_slot_symbol(i, j, simbolo)

            self.root.after(80, self._animar_giro_coluna, coluna, passos - 1, grade_final)
        else:
            for i in range(3):
                for j in range(3):
                    if j <= coluna:
                        simbolo = grade_final[i][j]
                    else:
                        simbolo = random.choices(self.symbols, weights=self.weights)[0]
                    self._set_slot_symbol(i, j, simbolo)

            if coluna < 2:
                self.root.after(100, self._animar_giro_coluna, coluna + 1, 12, grade_final)
            else:
                for i in range(3):
                    for j in range(3):
                        self._set_slot_symbol(i, j, grade_final[i][j])

                self._finalizar_giro_normal(grade_final)

    # ======================
    # MODO ESPECIAL
    # ======================

    def iniciar_modo_especial(self):
        if self.em_modo_especial or self.spin_em_andamento:
            return

        custo = self.aposta * 8
        if self.creditos < custo:
            self.result_label.config(
                text=f"Modo Especial exige {custo} créditos.", fg="red"
            )
            return

        self.em_modo_especial = True
        self.btn_spin.config(state="disabled")
        self.btn_special.config(state="disabled")

        self.gastar_creditos(custo)
        self.result_label.config(
            text="🔥 Modo Especial iniciado! 8 giros em sequência…", fg="gold"
        )

        self._rodar_modo_especial(restantes=8, total=0)

    def _rodar_modo_especial(self, restantes, total):
        grade = self._gerar_grade_final()
        for i in range(3):
            for j in range(3):
                self._set_slot_symbol(i, j, grade[i][j])

        premio, venceu, _ = self._calcular_premio(grade)

        if venceu:
            total += premio * self.multiplicador_especial

        if restantes > 1:
            self.result_label.config(
                text=f"Modo Especial: giros restantes {restantes-1} | ganho parcial {total}",
                fg="gold",
            )
            self.root.after(500, self._rodar_modo_especial, restantes - 1, total)
        else:
            self.ganhar_creditos(total)
            self.result_label.config(
                text=f"🔥 Modo Especial finalizado! Ganho total: {total}",
                fg="gold" if total > 0 else "white",
            )
            self.giros_vencedores = 0
            self.em_modo_especial = False
            self.btn_spin.config(state="normal")
            self.btn_special.config(state="disabled")

    # ======================
    # TESOURARIA / 1 DIA
    # ======================

    def simular_tesouraria(self):
        resultado = simular_tesouraria_taleb()

        self.cofre_seguro = resultado["capital_seguro_final"]
        self.cofre_dragao = resultado["capital_volatil_final"]
        self.jackpot = resultado["jackpot_final"]
        self._atualizar_painel_caixas()

        msg = (
            "Simulação Talebiana concluída:\n\n"
            f"Capital seguro final: R$ {resultado['capital_seguro_final']:,.2f}\n"
            f"Capital volátil final: R$ {resultado['capital_volatil_final']:,.2f}\n"
            f"Jackpot acumulado: R$ {resultado['jackpot_final']:,.2f}\n\n"
            f"Crescimento total: {resultado['crescimento_percentual']:.2f}%\n"
            f"Drawdown máximo: {resultado['drawdown_maximo']*100:.2f}%\n"
            f"Sharpe ratio: {resultado['sharpe_ratio']:.2f}"
        ).replace(",", "X").replace(".", ",").replace("X", ".")

        messagebox.showinfo("Simulação Talebiana", msg)

    def atualizar_um_dia(self):
        juros_diarios = 0.02 # ~2% ao dia
        self.cofre_seguro *= 1 + juros_diarios

        if self.cofre_dragao > 0:
            res = gerar_retorno_volatil(0.05, 0.20)
            retorno = res["retorno"]
            tipo = res["tipo"]

            capital_antes = self.cofre_dragao
            self.cofre_dragao *= 1 + retorno
            if self.cofre_dragao < 0:
                self.cofre_dragao = 0

            ganho = self.cofre_dragao - capital_antes

            if ganho > 0:
                self.jackpot += ganho
                self.cofre_dragao -= ganho
                resumo = f"Ganho volátil ({tipo}), jackpot +R$ {ganho:,.2f}"
            else:
                resumo = f"Perda volátil ({tipo}), cofre do dragão reduziu."
        else:
            resumo = "Cofre do dragão vazio hoje."

        self._atualizar_painel_caixas()
        self.result_label.config(
            text=f"Dia atualizado: juros no cofre seguro e risco no dragão. {resumo}",
            fg="gold",
        )


# ==============================
# EXECUÇÃO
# ==============================

if __name__ == "__main__":
    root = tk.Tk()
    app = CassinoSaudavelApp(root)
    root.mainloop()
