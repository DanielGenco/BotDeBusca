import os

def buscar_arquivos_por_nome(diretorio_raiz, termo_busca):
    resultados = []
    for raiz, _, arquivos in os.walk(diretorio_raiz):
        for arquivo in arquivos:
            if termo_busca.lower() in arquivo.lower():
                resultados.append(os.path.join(raiz, arquivo))
    return resultados

def abrir_arquivo(caminho):
    os.startfile(caminho)

print("📁 BOT DE BUSCA LOCAL")
diretorio_base = input("Digite o caminho da pasta onde a busca deve começar (ex: C:\\Users\\SeuNome\\Documents): ")

while True:
    termo = input("\nDigite o nome do arquivo/pasta (ou 'sair' para encerrar): ")
    if termo.lower() == 'sair':
        break

    encontrados = buscar_arquivos_por_nome(diretorio_base, termo)

    if not encontrados:
        print("⚠️ Nenhum arquivo encontrado.")
        continue

    print(f"\n✅ {len(encontrados)} resultado(s) encontrado(s):")
    for i, caminho in enumerate(encontrados, start=1):
        print(f"{i}. {caminho}")

    escolha = input("\nDigite o número do arquivo para abrir (ou Enter para ignorar): ")
    if escolha.isdigit():
        idx = int(escolha) - 1
        if 0 <= idx < len(encontrados):
            abrir_arquivo(encontrados[idx])
