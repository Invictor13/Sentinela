#  Sentinela Unimed 🛡️

O Sentinela é uma ferramenta de captura de evidências simples e segura, projetada para gravar a tela ou tirar screenshots de forma rápida e eficiente. Ideal para documentar processos, registrar bugs ou criar guias visuais.

## Funcionalidades

* **Captura de Tela:** Inicie um modo de captura e tire múltiplas screenshots com uma única tecla de atalho.
* **Gravação de Vídeo:** Grave a tela inteira, um monitor específico ou uma janela de aplicação individual.
* **Qualidade Ajustável:** Escolha entre perfis de gravação de "Alta Qualidade" (para textos nítidos) ou "Compacta" (para compartilhamento fácil).
* **Interface Intuitiva:** Uma janela principal clara e indicadores visuais para captura e gravação.
* **Atalhos Globais:** Opere o Sentinela mesmo quando ele estiver minimizado.
    * `Shift + F9`: Inicia o modo de captura / Tira uma screenshot.
    * `Shift + F10`: Abre a seleção de gravação / Para uma gravação em andamento.

## Pré-requisitos

* Python 3.8 ou superior.

## Instalação e Execução

1.  **Clone o Repositório:**
    ```bash
    git clone [URL_DO_SEU_REPOSITORIO]
    cd Sentinela
    ```

2.  **Instale as Dependências:**
    É altamente recomendado criar um ambiente virtual (`venv`) primeiro.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Execute a Aplicação:**
    Para garantir que todas as importações modulares funcionem corretamente, execute o projeto como um módulo a partir da raiz do diretório.
    ```bash
    python -m src.main
    ```

## Estrutura do Projeto

O projeto segue uma arquitetura modular para facilitar a manutenção e o desenvolvimento futuro, com responsabilidades separadas para UI, lógica de núcleo e configuração.

- /Sentinela
- /src
- /app
- /core
- /config
- /ui
- /assets
- main.py
- requirements.txt
- README.md


---
*Código forjado por Victor Ladislau Viana, com arquitetura supervisionada pela Forja Guará.*
