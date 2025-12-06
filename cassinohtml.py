import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import random
import math

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
# FUNÇÕES TALebianas (tesouraria antifrágil)
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
    """
    Simulação antifrágil Talebiana.
    Retorna dicionário com capitais finais e algumas métricas.
    """

    capital_seguro = capital_inicial * percentual_seguro
    capital_volatil = capital_inicial * percentual_volatil
    jackpot_simulado = 0.0

    historico_total = [capital_seguro + capital_volatil + jackpot_simulado]
    retornos_mensais = []
    eventos_cauda = []

    for mes in range(1, periodos + 1):
        # Renda fixa
        retorno_rf = random.uniform(retorno_mensal_rf_min, retorno_mensal_rf_max)
        capital_seguro *= 1 + retorno_rf

        # Aporte vai para parte volátil
        capital_volatil += aporte_mensal

        # Risco assimétrico
        resultado_volatil = gerar_retorno_volatil(
            retorno_volatil_media, retorno_volatil_desvio
        )

        retorno_vol = resultado_volatil["retorno"]
        tipo_evento = resultado_volatil["tipo"]

        capital_antes = capital_volatil
        capital_volatil *= 1 + retorno_vol
        capital_volatil = max(capital_volatil, 0)

        ganho_perdido = capital_volatil - capital_antes

        # 20% do ganho inesperado alimenta jackpot
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

        # ===== ECONOMIA BÁSICA =====
        self.saldo_dinheiro = 0.0
        self.cofre_seguro = 0.0
        self.cofre_dragao = 0.0
        self.jackpot = 10_000.0
        self.creditos = 500
        self.aposta = 10

        # 1 real = 1 crédito (ajusta se quiser outra relação)
        self.taxa_conversao = 1.0

        # Símbolos do slot
        self.symbols = ["dragao", "fogo", "orbe", "moeda", "lotos", "estrela"]
        self.weights = [3, 7, 10, 15, 20, 30]
        self.paytable = {
            "dragao": 30,
            "fogo": 15,
            "orbe": 10,
            "moeda": 6,
            "lotos": 4,
            "estrela": 2,
        }

        # Modo especial
        self.equilibrios_para_especial = 3
        self.multiplicador_especial = 2
        self.em_modo_especial = False
        self.giros_vencedores = 0

        # ===== CARREGAR IMAGENS =====
        self.symbol_images = {}
        for simbolo, arquivo in ARQUIVOS_SIMBOLOS.items():
            try:
                img = Image.open(arquivo).resize((80, 80), Image.LANCZOS)
                self.symbol_images[simbolo] = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Erro ao carregar {arquivo}: {e}")
                self.symbol_images[simbolo] = None

        # ===== TOPO (DRAGÃO) =====
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

        # ===== PAINEL DE CAIXAS =====
       self._criar_painel_caixas()
        self._atualizar_painel_caixas()

        # Área para depósito e conversão em créditos
        self._criar_area_deposito()
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
        """Lê o valor digitado no campo e converte para float."""
        texto = self.entry_deposito.get().strip().replace(",", ".")
        if not texto:
            return None
        try:
            return float(texto)
        except ValueError:
            return None

    def depositar(self):
        """Simula depósito em dinheiro no saldo."""
        valor = self._ler_valor_entry()
        if valor is None or valor <= 0:
            self.result_label.config(
                text="Informe um valor válido para depósito.",
                fg="red",
            )
            return

        self.saldo_dinheiro += valor
        self._atualizar_painel_caixas()
        self.entry_deposito.delete(0, tk.END)

        self.result_label.config(
            text=f"Depósito de R$ {valor:.2f} realizado com sucesso.",
            fg="gold",
        )

    def converter_para_creditos(self):
        """
        Converte dinheiro em créditos.
        - Se tiver valor digitado, usa esse valor.
        - Se estiver em branco, converte TODO o saldo.
        """
        valor = self._ler_valor_entry()
        if valor is None:
            valor = self.saldo_dinheiro # converte tudo se não informar

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



        # ===== INFO DO MODO ESPECIAL =====
        self.info_label = tk.Label(
            root,
            text=self._texto_info(),
            font=("Arial", 10),
            fg="white",
            bg="#8A0000",
            wraplength=380,
            justify="center",
        )
        self.info_label.pack(pady=6)

        # ===== SLOTS =====
        frame_slots = tk.Frame(root, bg="#8A0000")
        frame_slots.pack(pady=10)

        self.slots = []
        for i in range(3):
            linha = []
            for j in range(3):
                lbl = tk.Label(frame_slots, bg="#8A0000")
                lbl.grid(row=i, column=j, padx=8, pady=6)
                linha.append(lbl)
            self.slots.append(linha)

        # ===== BOTÕES =====
        self.btn_spin = tk.Button(
            root,
            text="INICIAR FLUXO",
            font=("Arial", 16, "bold"),
            bg="gold",
            fg="black",
            command=self.spin,
        )
        self.btn_spin.pack(pady=8)

        self.btn_special = tk.Button(
            root,
            text="MODO ESPECIAL (8 GIROS)",
            font=("Arial", 12, "bold"),
            bg="#FFD700",
            fg="black",
            state="disabled",
            command=self.iniciar_modo_especial,
        )
        self.btn_special.pack(pady=4)

        self.btn_simular_tesouraria = tk.Button(
            root,
            text="📊 Simular Tesouraria Taleb",
            font=("Arial", 11, "bold"),
            bg="#444",
            fg="white",
            command=self.simular_tesouraria,
        )
        self.btn_simular_tesouraria.pack(pady=4)

        self.btn_link = tk.Button(
            root,
            text="🔗 Código do Caos",
            font=("Arial", 11, "bold"),
            bg="#444",
            fg="white",
            command=self.abrir_link,
        )
        self.btn_link.pack(pady=4)

        # ===== RESULTADO =====
        self.result_label = tk.Label(
            root,
            text="Clique em INICIAR FLUXO.",
            font=("Arial", 12),
            fg="white",
            bg="#8A0000",
            wraplength=380,
            justify="center",
        )
        self.result_label.pack(pady=8)

    # ======================
    # ECONOMIA / CAIXAS
    # ======================

    def gastar_creditos(self, valor):
        self.creditos -= valor
        self._atualizar_painel_caixas()

    def ganhar_creditos(self, valor):
        self.creditos += valor
        self._atualizar_painel_caixas()

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
                font=("Arial", 9, "bold"),
                fg="white",
                bg="#5B0000",
            ).pack()
            lbl_valor = tk.Label(
                frame,
                text="R$ 0,00",
                font=("Arial", 11, "bold"),
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

    def _texto_info(self):
        return (
            f"Modo Especial após {self.equilibrios_para_especial} giros vencedores.\n"
            f"No modo especial, cada linha vencedora paga x{self.multiplicador_especial}."
        )

    # ======================
    # INTERFACE
    # ======================

    def abrir_link(self):
        import webbrowser

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
    # MOTOR DO SLOT
    # ======================

    def _girar_grade(self):
        grade = []
        for i in range(3):
            linha = []
            for j in range(3):
                simbolo = random.choices(self.symbols, weights=self.weights)[0]
                linha.append(simbolo)

                img = self.symbol_images[simbolo]
                if img:
                    self.slots[i][j].config(image=img, text="")
                    self.slots[i][j].image = img
                else:
                    self.slots[i][j].config(text=simbolo, fg="white", image="")
            grade.append(linha)
        return grade

    def _calcular_premio(self, grade):
        premio = 0
        venceu = False

        linhas = []
        linhas.extend(grade) # horizontais
        linhas.extend([[grade[i][j] for i in range(3)] for j in range(3)]) # verticais
        linhas.append([grade[i][i] for i in range(3)]) # diagonal principal
        linhas.append([grade[i][2 - i] for i in range(3)]) # diagonal secundária

        for linha in linhas:
            if linha[0] == linha[1] == linha[2]:
                venceu = True
                simbolo = linha[0]
                premio += self.aposta * self.paytable.get(simbolo, 0)

        return premio, venceu

    # ======================
    # GIRO NORMAL
    # ======================

    def spin(self):
        if self.em_modo_especial:
            return

        if self.creditos < self.aposta:
            self.result_label.config(
                text="Créditos insuficientes para girar. 💸", fg="red"
            )
            return

        self.gastar_creditos(self.aposta)

        grade = self._girar_grade()
        premio, venceu = self._calcular_premio(grade)

        if venceu:
            self.giros_vencedores += 1
            self.ganhar_creditos(premio)
            self.result_label.config(
                text=f"✨ Você ganhou {premio} créditos!", fg="gold"
            )
        else:
            self.result_label.config(
                text="Nenhuma linha vencedora desta vez.", fg="white"
            )

        if self.giros_vencedores >= self.equilibrios_para_especial:
            self.btn_special.config(state="normal")

    # ======================
    # MODO ESPECIAL
    # ======================

    def iniciar_modo_especial(self):
        if self.em_modo_especial:
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
        grade = self._girar_grade()
        premio, venceu = self._calcular_premio(grade)

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
    # BOTÃO: SIMULAR TESOURARIA
    # ======================

    def simular_tesouraria(self):
        resultado = simular_tesouraria_taleb()

        # Atualiza cofres + jackpot com números finais
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


# ==============================
# EXECUÇÃO
# ==============================

if __name__ == "__main__":
    root = tk.Tk()
    app = CassinoSaudavelApp(root)
    root.mainloop()

