import customtkinter as ctk
import subprocess
import os
import requests
import sys
import tkinter as tk
import tkinter.messagebox
import re

# --- Configurações da GUI ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# --- Variáveis e Caminhos ---
PALORNI_FOLDER = "C:\\palorni"

# URLs dos recursos (não é mais necessário baixar o arquivo .pow do plano de energia)
RESOURCES = {
    "Autoruns.exe": "https://raw.githubusercontent.com/exm4L/EXM-FREE-UTILITY-RESCOURSES/refs/heads/main/Autoruns.exe",
    "Nvidia_Porfile_Inspector_2.4.0.27.exe": "https://raw.githubusercontent.com/exm4L/EXM-10.0-Resources/refs/heads/main/nvidiaProfileInspector_2.4.0.27.exe",
    "Windows_Update_Blocker.exe": "https://raw.githubusercontent.com/exm4L/EXM-FREE-UTILITY-RESCOURSES/refs/heads/main/Windows_Update_Blocker.exe"
}

# --- Funções de Lógica e Execução ---

def run_admin_check():
    """Verifica se o script está rodando com privilégios de administrador."""
    try:
        temp_dir = 'C:\\AdminCheckTempDir'
        os.makedirs(temp_dir, exist_ok=True)
        os.rmdir(temp_dir)
        return True
    except PermissionError:
        return False
    except Exception:
        return False

def check_resources():
    """Verifica se a pasta PALORNI_FOLDER e os recursos existem."""
    if not os.path.exists(PALORNI_FOLDER):
        return False
    
    for filename in RESOURCES:
        if not os.path.exists(os.path.join(PALORNI_FOLDER, filename)):
            return False
            
    return True

def download_resource(filename, url, progress_callback):
    """Baixa um único recurso."""
    filepath = os.path.join(PALORNI_FOLDER, filename)
    try:
        os.makedirs(PALORNI_FOLDER, exist_ok=True)
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total_size)
        return True
    except Exception as e:
        tkinter.messagebox.showerror("Erro de Download", f"Falha ao baixar {filename}. Verifique sua conexão. Erro: {e}")
        return False

def execute_system_command(command, success_msg, error_msg):
    """Função genérica para executar comandos do sistema de forma robusta e com feedback."""
    try:
        result = subprocess.run(
            command, 
            check=True, 
            shell=True,
            capture_output=True, 
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if success_msg:
            tkinter.messagebox.showinfo("Sucesso", success_msg)
        return True
    
    except subprocess.CalledProcessError as e:
        error_detail = e.stderr or e.stdout or "Nenhum detalhe de erro fornecido."
        tkinter.messagebox.showerror("Erro de Execução", f"{error_msg}\nDetalhe: {error_detail.strip()}")
        return False
    except Exception as e:
        tkinter.messagebox.showerror("Erro Desconhecido", f"Ocorreu um erro: {e}")
        return False

# --- Classe Principal da Aplicação ---
class PalorniTweeksApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Palorni Tweeks")
        self.geometry("1000x800")

        # AVISO DE ADMIN: Se falhar, AINDA TENTA ABRIR O GUI.
        self.is_admin = run_admin_check()
        if not self.is_admin:
            self.show_admin_error()

        # Frame principal com scroll para manter tudo em uma única "aba"
        # Frame principal com fundo preto e scroll
        main_frame = ctk.CTkFrame(self, fg_color="#000000")
        main_frame.pack(padx=12, pady=10, fill="both", expand=True)

        # Canvas (tkinter) + Scrollbar (CTk) + frame interno (CTk)
        canvas = tk.Canvas(main_frame, bg="#000000", highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(main_frame, orientation="vertical", command=canvas.yview)
        scrollable_frame = ctk.CTkFrame(canvas, fg_color="#000000")

        # atualizar scrollregion quando o conteúdo mudar
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # criar janela dentro do canvas e garantir que seu width acompanhe o canvas
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def _on_canvas_config(event):
            # ajustar a largura do frame interno para o width do canvas (responsividade)
            try:
                canvas.itemconfig(canvas_window, width=event.width)
            except Exception:
                pass

        canvas.bind("<Configure>", _on_canvas_config)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Habilitar rolagem com roda do mouse apenas quando o cursor estiver sobre o canvas
        def _on_mousewheel(event):
            try:
                if sys.platform == 'win32':
                    delta = int(-1 * (event.delta / 120))
                    canvas.yview_scroll(delta, "units")
                elif sys.platform == 'darwin':
                    canvas.yview_scroll(int(-1 * event.delta), "units")
                else:
                    if hasattr(event, 'num'):
                        if event.num == 4:
                            canvas.yview_scroll(-1, "units")
                        elif event.num == 5:
                            canvas.yview_scroll(1, "units")
            except Exception:
                pass

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        canvas.bind("<Button-4>", _on_mousewheel)
        canvas.bind("<Button-5>", _on_mousewheel)

        # Título principal e subtítulo com espaçamento amigável
        ctk.CTkLabel(scrollable_frame, text="Palorni Tweeks", font=ctk.CTkFont(size=28, weight="bold"), text_color="white").pack(pady=(12, 2))
        ctk.CTkLabel(scrollable_frame, text="Coleção de ajustes para desempenho e manutenção do sistema\nUse com cuidado — algumas ações exigem administrador.",
                      font=ctk.CTkFont(size=12), text_color="#bfc7cd").pack(pady=(0, 18))

        # Carregar todo o conteúdo dentro do mesmo frame scrollable
        self.load_setup_content(scrollable_frame)
        ctk.CTkLabel(scrollable_frame, text="", font=ctk.CTkFont(size=6), text_color="#bfc7cd").pack()
        self.load_general_content(scrollable_frame)
        ctk.CTkLabel(scrollable_frame, text="", font=ctk.CTkFont(size=6), text_color="#bfc7cd").pack()
        self.load_power_content(scrollable_frame)
        ctk.CTkLabel(scrollable_frame, text="", font=ctk.CTkFont(size=6), text_color="#bfc7cd").pack()
        self.load_gpu_content(scrollable_frame)
        ctk.CTkLabel(scrollable_frame, text="", font=ctk.CTkFont(size=6), text_color="#bfc7cd").pack()
        self.load_clean_storage_content(scrollable_frame)
        ctk.CTkLabel(scrollable_frame, text="", font=ctk.CTkFont(size=6), text_color="#bfc7cd").pack()
        self.load_additional_content(scrollable_frame)

    # --- Métodos de Interface e Layout ---

    def show_admin_error(self):
        # Aviso na inicialização, mas não destrói a GUI imediatamente
        tkinter.messagebox.showwarning("Aviso de Permissão", "O utilitário NÃO está rodando como Administrador. Algumas funções não funcionarão.")

    def create_content_frame(self, tab):
        """Cria um frame interno com layout de grade para organizar botões."""
        frame = ctk.CTkFrame(tab, fg_color="transparent")
        frame.pack(padx=10, pady=10, fill="both", expand=True)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        return frame
    
    def create_button(self, parent, text, command, row, col, columnspan=1, rowspan=1, sticky="ew"):
        """Cria um botão maior e posicionado em grid. Retorna o widget (não None)."""
        btn = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            height=45,
            fg_color="#6a0dad",
            hover_color="#7f3fbf",
            text_color="white",
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        btn.grid(row=row, column=col, columnspan=columnspan, rowspan=rowspan, padx=15, pady=10, sticky=sticky)
        return btn


    # --- Conteúdo das Abas ---

    def load_setup_content(self, tab):
        frame = self.create_content_frame(tab)
        ctk.CTkLabel(frame, text="Preparação do Sistema e Recursos Necessários", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, columnspan=2, pady=15, sticky="n")

        # Seção 1: Recursos
        status_text = "✅ Recursos OK" if check_resources() else f"❌ Recursos faltando (Pasta: {PALORNI_FOLDER})"
        self.resource_status_label = ctk.CTkLabel(frame, text=status_text, font=ctk.CTkFont(size=13))
        self.resource_status_label.grid(row=1, column=0, columnspan=2, pady=(0, 5))

        self.resource_progress_bar = ctk.CTkProgressBar(frame, orientation="horizontal", width=400)
        self.resource_progress_bar.set(0)
        self.resource_progress_bar.grid(row=2, column=0, columnspan=2, pady=(0, 15))
        
        self.create_button(frame, "1. Baixar/Atualizar Arquivos de Otimização 📥", self.download_all_resources, row=3, col=0, columnspan=2)
        
        ctk.CTkLabel(frame, text="--- Ponto de Restauração ---", font=ctk.CTkFont(size=16, weight="bold")).grid(row=4, column=0, columnspan=2, pady=(25, 5))

        # Seção 2: Restauração
        self.create_button(frame, "2. Criar Ponto de Restauração AGORA 🔄", self.create_restore_point, row=5, col=0)
        self.create_button(frame, "3. Abrir Restauração do Windows 🔁", self.open_restore_ui, row=5, col=1)
        self.create_button(frame, "Sair do Palorni Tweeks ❌", self.quit, row=6, col=0)


    def load_general_content(self, tab):
        frame = self.create_content_frame(tab)
        ctk.CTkLabel(frame, text="Otimizações do Sistema Operacional e Serviços", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, columnspan=2, pady=15, sticky="n")
        
        row_index = 1
        
        # Telemetria
        self.create_button(frame, "Desabilitar Telemetria e Coleta de Dados 🕵️", 
                      command=lambda: execute_system_command(
                          "reg add HKLM\\Software\\Policies\\Microsoft\\Windows\\DataCollection /v AllowTelemetry /t REG_DWORD /d 0 /f",
                          "Telemetria desabilitada. (Necessita de Reinicialização)",
                          "Falha ao desabilitar telemetria."
                      ), row=row_index, col=0)
        
        # Superfetch/Sysmain
        self.create_button(frame, "Desabilitar Serviço Superfetch/Sysmain (Reduz uso de RAM) 🛑", 
                      command=lambda: execute_system_command(
                          "sc config SysMain start= disabled",
                          "Serviço Sysmain desabilitado.",
                          "Falha ao desabilitar Sysmain."
                      ), row=row_index, col=1)
        
        row_index += 1
        # Windows Update Blocker
        wub_path = os.path.join(PALORNI_FOLDER, "Windows_Update_Blocker.exe")
        self.create_button(frame, "Abrir Windows Update Blocker (Bloqueia atualizações) 🔒",
                           command=lambda: os.startfile(wub_path) if os.path.exists(wub_path) else tkinter.messagebox.showerror("Erro", "Windows Update Blocker não encontrado. Baixe na Configuração Inicial."), 
                           row=row_index, col=0)
        
        # Otimização de Rede
        self.create_button(frame, "Otimização de Desempenho de Rede (Throttling) 🌐",
                           command=lambda: execute_system_command(
                               "reg add HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile /v NetworkThrottlingIndex /t REG_DWORD /d 10 /f",
                               "Otimização de rede aplicada.",
                               "Falha na otimização de rede."
                           ), row=row_index, col=1)


    def load_power_content(self, tab):
        frame = self.create_content_frame(tab)
        ctk.CTkLabel(frame, text="Gerenciamento de Energia e Desempenho da CPU", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, columnspan=2, pady=15, sticky="n")
        
        # Plano de Energia
        self.create_button(frame, "Aplicar Plano de Energia Palorni Tweeks ⚡", self.apply_power_plan, row=1, col=0)
        self.create_button(frame, "Restaurar para Padrão (Equilibrado)", self.set_default_power_plan, row=1, col=1)
        
        # Opções de CPU
        ctk.CTkLabel(frame, text="--- Otimizações de CPU ---", font=ctk.CTkFont(size=16, weight="bold")).grid(row=2, column=0, columnspan=2, pady=(25, 5))
        
        self.create_button(frame, "Abrir Ferramentas de Gerenciamento de Energia (Avançado) ⚙️", 
                           command=lambda: subprocess.run("powercfg.cpl", shell=True), row=3, col=0)
        
        self.create_button(frame, "Outra Otimização de CPU (Regedit) 📈", 
                           command=lambda: tkinter.messagebox.showinfo("Em Breve", "Mais otimizações complexas de CPU serão adicionadas."), row=3, col=1)


    def load_gpu_content(self, tab):
        frame = self.create_content_frame(tab)
        ctk.CTkLabel(frame, text="Otimizações de GPU e Vídeo (NVIDIA)", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, columnspan=2, pady=15, sticky="n")
        
        nvpi_path = os.path.join(PALORNI_FOLDER, "Nvidia_Porfile_Inspector_2.4.0.27.exe")
        nvpi_config = os.path.join(PALORNI_FOLDER, "EXM_Free_NVPI_V10.nip")
        
        if not os.path.exists(nvpi_path) or not os.path.exists(nvpi_config):
            ctk.CTkLabel(frame, text="⚠️ Arquivos NVPI ou Config (.nip) não encontrados. Baixe na aba 'Configuração Inicial'.", text_color="red", font=ctk.CTkFont(size=14)).grid(row=1, column=0, columnspan=2, pady=10)
        else:
            command = f'"{nvpi_path}" -importFile "{nvpi_config}"'
            self.create_button(frame, "Aplicar Perfil Nvidia Inspector (Recomendado) 🖥️", 
                           command=lambda: execute_system_command(
                               command, 
                               "Comando de aplicação do perfil NVPI enviado.",
                               "Falha ao iniciar o Nvidia Profile Inspector ou aplicar o perfil."
                           ), row=2, col=0)
        
        self.create_button(frame, "Abrir Painel de Controle NVIDIA", 
                           command=lambda: os.startfile("C:\\Program Files\\NVIDIA Corporation\\Control Panel Client\\nvcplui.exe"), row=2, col=1)


    def load_clean_storage_content(self, tab):
        frame = self.create_content_frame(tab)
        ctk.CTkLabel(frame, text="Limpeza de Arquivos e Otimização de Armazenamento", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, columnspan=2, pady=15, sticky="n")
        
        # Limpeza
        self.create_button(frame, "Limpeza de Disco Avançada (Cleanmgr) 🧹", 
                      command=lambda: execute_system_command("cleanmgr /sageset:1 & cleanmgr /sagerun:1", 
                                                             "Comando de limpeza iniciado.", 
                                                             "Falha ao iniciar o Cleanmgr."), row=1, col=0)
        
        # Limpar %temp%
        self.create_button(frame, "Limpar Arquivos Temporários (%temp%)", 
                      command=lambda: execute_system_command(
                          f"del /f /s /q {os.path.join(os.environ['TEMP'], '*')}", 
                          "Arquivos temporários excluídos.", 
                          "Falha ao excluir arquivos temporários."
                      ), row=1, col=1)

        ctk.CTkLabel(frame, text="--- Otimização de Unidades ---", font=ctk.CTkFont(size=16, weight="bold")).grid(row=2, column=0, columnspan=2, pady=(25, 5))
        
        # Otimizador de Unidades
        self.create_button(frame, "Otimizador de Unidades (Desfragmentação) 🗃️", 
                      command=lambda: os.startfile("dfrgui.exe"), row=3, col=0)
        
        # Resetar Cache de Icones
        self.create_button(frame, "Reconstruir Cache de Ícones do Sistema",
                           command=lambda: execute_system_command(
                               "taskkill /f /im explorer.exe & attrib -h -s /d %LocalAppData%\\IconCache.db & del /f %LocalAppData%\\IconCache.db & start explorer",
                               "Cache de ícones reconstruído. (Pode demorar um pouco)",
                               "Falha ao reconstruir cache de ícones."
                           ), row=3, col=1)

    def load_additional_content(self, tab):
        frame = self.create_content_frame(tab)
        ctk.CTkLabel(frame, text="Configurações Avançadas e Qualidade de Vida", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, columnspan=2, pady=15, sticky="n")
        
        # UAC
        self.create_button(frame, "Desabilitar Controle de Conta de Usuário (UAC) 🛑", 
                      command=lambda: execute_system_command(
                          "reg add HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System /v EnableLUA /t REG_DWORD /d 0 /f",
                          "UAC desabilitado. Necessário reiniciar.",
                          "Falha ao desabilitar UAC."
                      ), row=1, col=0)
                      
        # Extensões de arquivo
        self.create_button(frame, "Mostrar Extensões de Arquivo 📝", 
                      command=lambda: execute_system_command(
                          "reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced /v HideFileExt /t REG_DWORD /d 0 /f",
                          "Extensões de arquivo agora visíveis.",
                          "Falha ao mostrar extensões."
                      ), row=1, col=1)
        
        # Autoruns
        autoruns_path = os.path.join(PALORNI_FOLDER, "Autoruns.exe")
        self.create_button(frame, "Abrir Gerenciador de Inicialização (Autoruns) 📈", 
                           command=lambda: os.startfile(autoruns_path) if os.path.exists(autoruns_path) else tkinter.messagebox.showerror("Erro", "Autoruns.exe não encontrado. Baixe na Configuração Inicial."), row=2, col=0)


    # --- Métodos de Execução (Lógica do Sistema) ---

    def download_all_resources(self):
        self.resource_status_label.configure(text="Status: Baixando recursos... ⏳")
        self.resource_progress_bar.set(0)

        total_files = len(RESOURCES)
        
        for i, (filename, url) in enumerate(RESOURCES.items()):
            self.resource_status_label.configure(text=f"Status: Baixando {filename} ({i+1}/{total_files})...")
            self.update_idletasks()

            def update_progress(downloaded, total_size):
                if total_size > 0:
                    overall_progress = (i + downloaded / total_size) / total_files
                    self.resource_progress_bar.set(overall_progress)
                self.update_idletasks()
            
            if not download_resource(filename, url, update_progress):
                self.resource_status_label.configure(text="Status: ❌ Download interrompido devido a erro.")
                return

        self.resource_status_label.configure(text="Status: ✅ Todos os recursos baixados com sucesso!")
        self.resource_progress_bar.set(1)
        tkinter.messagebox.showinfo("Sucesso", f"Todos os recursos foram baixados para {PALORNI_FOLDER}!")

    def create_restore_point(self):
        command = 'powershell Checkpoint-Computer -Description "Palorni Tweeks Restore Point"'
        execute_system_command(command, "Ponto de restauração criado com sucesso!", "Falha ao criar o ponto de restauração.")

    def open_restore_ui(self):
        try:
            subprocess.run("rstrui.exe", check=True, shell=True)
        except:
            tkinter.messagebox.showerror("Erro", "Falha ao abrir o rstrui.exe.")

    def apply_power_plan(self):
        """Executa o pipeline PowerShell pedido para duplicar e renomear o esquema para 'Palorni Plan', então ativa-o.

                Comando usado (PowerShell):
                powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61 |
                    Select-String -Pattern '[\\da-f]{8}-([\\da-f]{4}-){3}[\\da-f]{12}' -AllMatches |
                    ForEach-Object { $NewGuid = $_.Matches.Value; powercfg /changename $NewGuid "Palorni Plan"; Write-Output $NewGuid }
        """
        try:
            # PowerShell pipeline requested by user; use [0-9a-f] to avoid backslash escapes
            ps_pipeline = (
                'powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61 | '
                "Select-String -Pattern '[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}' -AllMatches | "
                'ForEach-Object { $NewGuid = $_.Matches.Value; powercfg /changename $NewGuid "Palorni" "Otimizado para alto desempenho em jogos competitivos (eSports)"; Write-Output $NewGuid }'
            )

            # Call PowerShell directly without shell=True to avoid escaping issues
            result = subprocess.run([
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                ps_pipeline
            ], check=True, capture_output=True, text=True)

            output = (result.stdout or "").strip()
            guids = re.findall(r'([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})', output)
            if not guids:
                # Fallback: listar esquemas e pegar o último GUID
                list_result = subprocess.run(["powercfg", "-list"], check=True, capture_output=True, text=True)
                list_out = list_result.stdout or ""
                guids = re.findall(r'([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})', list_out)

            if guids:
                guid = guids[-1]
                subprocess.run(["powercfg", "/setactive", guid], check=True)
                tkinter.messagebox.showinfo("Sucesso", "Palorni criado, renomeado e ativado com sucesso.")
            else:
                tkinter.messagebox.showerror("Erro", f"Comando executado, mas não foi possível obter o GUID.\nOutput:\n{output}")

        except subprocess.CalledProcessError as e:
            err = e.stderr or e.stdout or str(e)
            tkinter.messagebox.showerror("Erro de PowerCfg", f"Falha ao criar/renomear/ativar o plano de energia. Erro: {err}")
        except Exception as e:
            tkinter.messagebox.showerror("Erro Desconhecido", f"Ocorreu um erro: {e}")

    def set_default_power_plan(self):
        BALANCED_GUID = "381b4222-f694-41f0-9685-ff5bb260df2e" 
        execute_system_command(f"powercfg /setactive {BALANCED_GUID}", "Plano de Energia restaurado para 'Equilibrado'.", "Falha ao restaurar o plano.")
            
    def quit(self):
        self.destroy()

if __name__ == "__main__":
    app = PalorniTweeksApp()
    if app.winfo_exists():
        app.mainloop()