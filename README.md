# Referências de UI no Pinterest

Base privada com **11.236 imagens distintas**, organizadas em **20 macroáreas**, a partir de **793 páginas de origem**.

- [Base completa em JSON](data/references.json), com caminhos locais, URLs e estado do download.
- [Exportação CSV](exports/referencias_ui.csv).
- [Exportação JSON](exports/referencias_ui.json).
- [Pacote exportável ZIP](exports/base_ui_exportavel.zip).
- [Imagens por macroárea](images/).
- [Planilha online](https://docs.google.com/spreadsheets/d/1ZWwUpsseGXfKOrHad4wzGtBz8UV0rlT6DKb1f8c8y-c/edit).

As imagens baixadas ficam em `images/<macroarea>/<id>.<extensão>`, preservando os arquivos disponíveis na fonte. O campo `local_path` permite relacionar cada arquivo aos metadados e à página de origem. O manifesto registra o resultado efetivo de cada download.

## Consulta e exportação

Abra a pasta `images` no GitHub para visualizar os arquivos online. Clone o repositório ou use **Code > Download ZIP** para exportar a base e as imagens. CSV e JSON também podem ser baixados separadamente em `exports`.

## Critérios e limites

Uma referência corresponde a uma imagem distinta, deduplicada pela assinatura do arquivo. A classificação é automática pelo nome da coletânea, tópico ou consulta. Não houve revisão visual individual de todos os registros. Recortes ou arquivos diferentes de um mesmo projeto podem permanecer.

O Pinterest não expõe o título nem o link individual de todos os pins em páginas públicas. As ausências foram preservadas; cada registro mantém o link da imagem e a página de origem. Os direitos das imagens permanecem com seus respectivos titulares; este repositório não concede licença sobre elas.

Consulta realizada em 22/10/2026, America/Sao_Paulo. Carimbos individuais de coleta em UTC.
