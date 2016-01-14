Nome: João Paulo F. Brito

Relatório do Projeto Final – Tópicos em Recuperação de Informação


## 1. Objetivo

O objetivo deste trabalho é implementar uma máquina de busca para a CFC (Cystic
Fibrosis Collection), que pode ser encontrada em:
http://coyote.icomp.ufam.edu.br/ir/cfc.tar.gz.


## 2. Implementação e uso

O trabalho foi implementado em python 2.7, e testado usando o S.O. Ubuntu 14.04
LTS. O repositório git com o projeto pode ser acessado pelo link:
https://github.com/jpaulofb/cfc_search_engine_tri.

### 2.1. Descrição geral das estruturas de dados e arquivos

- `main.py`: script principal do projeto, fornece uma interface com o usuário
  para o uso das outras classes.

- `SearchEngine.py`: script contém a classe da máquina de busca. Nela estão os
  atributos do índice invertido, e dados dos documentos da coleção. A classe
  Parser é um de seus atributos.

- `Parser.py`: script que contém a classe Parser, responsável por ler e traduzir
  os arquivos da CFC em dados utilizados pela máquina de busca, além de fazer a
  tokenização e remoção de stop words.

- `Evaluator.py`: script que agrega as funções de avaliação de resultados.

- `util.py`: script com definições de objetos comuns, usados pelos demais
  scripts, como por exemplo definições de beans para documentos e consultas.

- `sw.txt`: arquivo de definição de stop words, lido pela classe Parser.

- `cfcIndex.txt`: arquivo padrão em que é salvo depois de criado na classe
  SearchEngine, nele ficarão salvos dados relevantes dos documentos, e o índice
  invertido em si.

### 2.2. Uso do programa

O projeto tem 3 funcionalidades principais:

- criar e salvar o índice invertido, a partir de uma **pasta** com os arquivos
  da coleção.  Ex: `python main.py createindex -in <path>`, Onde `<path>` é o
  caminho para a pasta onde os arquivos da coleção estão, espera-se que os
  nomes dos arquivos sejam do tipo *"cf/d{2}"*

- processar o arquivo de consultas da coleção. Ex: `python main.py queryfile
  -in <path> [-rs val]`, Onde `<path>` é o caminho para o arquivo de consultas
  da coleção, `[-rs num]` é um argumento opcional que define a quantidade
  máxima de resultados retornados pela consulta, o valor padrão é 20. O
  programa então mostrará as métricas de avaliação P@10, e MAP, e o tempo de
  processamento para cada consulta. Ao final mostra as médias das métricas.

- modo de consulta interativa, em que o usuário pode digitar sua consulta e
  receber os resultados da consulta na tela. Ex: ``python main.py iquery [-rs
  num]``, Neste modo o terminal esperará que o usuário digite uma consulta e
  mostrará o resultado para a consulta, e esperará uma nova consulta, para sair
  basta digitar ``CTRL+D`` ou ``CTRL+C``.

Digitando ``python main.py -h`` mostra uma ajuda simples do programa.

### 2.3. Algumas decisões de implementação

Com relação ao parse do arquivo, considerou-se como palavra apenas sequências
contíguas de letras, assim, palavras com hífen ou apóstrofo foram considerados
como palavras distintas. A decisão foi tomada porque observou-se a formação de
palavras com hífen que na verdade não eram uma só palavra e que ocorriam apenas
uma vez na coleção.

Os atributos considerados relevantes para gerar o índice foram:

- **TI**: Título.

- **MJ**: assuntos principais.

- **MN**: assuntos secundários.

- **AB** ou **EX**: abstract, ou excerpt, quando presentes.

Para melhorar o desempenho do processamento da consulta, a consulta não retorna
todos os documentos, mas sim um limite, que pode ser  mudado através de um
argumento do método ``process_query`` da classe ``SearchEngine``. Um heap com
os documentos de maior similaridade é mantido, de forma que não é preciso fazer
um sort na similaridade de todos os documentos.

## 3. Resultados

Usando a funcionalidade para processar o arquivo de consultas da coleção, e com
o máximo de 20 documentos retornados na consulta, as médias das métricas de
avaliação para as consultas podem ser vistas na tabela a seguir.

| Métrica                                | Valor   |
|----------------------------------------|---------|
| P@10                                   | 0.48000 |
| MAP interpolado                        | 0.15173 |
| Tempo de processamento de consulta (s) | 0.00133 |

Os pontos de revocação interpolados médios podem ser vistos na tabela a seguir:

| Revocação | Precisão |
|:---------:|:--------:|
|  0.00000  |  0.85412 |
|  0.10000  |  0.61309 |
|  0.20000  |  0.44412 |
|  0.30000  |  0.22333 |
|  0.40000  |  0.12860 |
|  0.50000  |  0.06537 |
|  0.60000  |  0.02945 |
|  0.70000  |  0.00667 |
|  0.80000  |  0.00667 |
|  0.90000  |  0.00000 |
|  1.00000  |  0.00000 |
