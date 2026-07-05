# Trabalho de Redes 2

Implementação didática de comunicação TCP cliente-servidor em Python para
transferência de arquivos com validação de integridade por SHA-256.

O projeto demonstra como criar um protocolo simples de aplicação sobre TCP:
o cliente envia metadados do arquivo, transmite o conteúdo em blocos e aguarda
uma resposta de confirmação do servidor.

## Estrutura do projeto

- `servidor.py`: abre um socket TCP, recebe arquivos, valida o protocolo,
  confere o hash SHA-256 e salva os arquivos em `arquivos_recebidos/`.
- `cliente.py`: conecta ao servidor, calcula o hash SHA-256 do arquivo, envia
  um cabeçalho binário e transmite o conteúdo em blocos.

## Requisitos

- Python 3.8 ou superior.
- Nenhuma dependência externa é necessária.

## Como executar

Abra um terminal e inicie o servidor:

```bash
python servidor.py
```

Por padrão, o servidor escuta em `0.0.0.0:5000`.

Em outro terminal, envie um arquivo com o cliente:

```bash
python cliente.py 127.0.0.1 5000 caminho/do/arquivo.ext
```

Exemplo:

```bash
python cliente.py 127.0.0.1 5000 documento.pdf
```

Se a transferência for concluída e o hash do arquivo estiver correto, o arquivo
será salvo no diretório `arquivos_recebidos/`.

## Fluxo da transferência

1. O cliente valida se o arquivo existe.
2. O cliente calcula o hash SHA-256 do conteúdo.
3. O cliente envia um cabeçalho binário com os metadados da transferência.
4. O cliente envia o nome do arquivo em UTF-8.
5. O cliente envia o conteúdo do arquivo em blocos.
6. O servidor recebe o arquivo em um arquivo temporário `.part`.
7. O servidor compara o hash recebido com o hash calculado localmente.
8. Se a validação passar, o servidor move o arquivo para o destino final.
9. O servidor responde ao cliente com sucesso ou erro.

## Protocolo da aplicação

Antes do conteúdo do arquivo, o cliente envia um cabeçalho binário no formato
`!4sBHQ32s`, definido pelo módulo `struct`:

- `4s`: identificador do protocolo, sempre `TRED`;
- `B`: versão do protocolo, atualmente `1`;
- `H`: tamanho do nome do arquivo em bytes;
- `Q`: tamanho do arquivo em bytes;
- `32s`: hash SHA-256 esperado do conteúdo.

Depois do cabeçalho, o cliente envia:

1. o nome do arquivo codificado em UTF-8;
2. o conteúdo do arquivo como fluxo de bytes.

A resposta do servidor usa o formato `!BH` seguido da mensagem:

- `B`: status da operação, sendo `0` para sucesso e `1` para erro;
- `H`: tamanho da mensagem em bytes;
- mensagem em UTF-8.

## Validações implementadas

- Identificador e versão do protocolo.
- Tamanho do nome do arquivo.
- Limite máximo de arquivo de 100 MB no servidor.
- Sanitização básica do nome do arquivo recebido.
- Verificação de integridade com SHA-256.
- Remoção de arquivo temporário em caso de erro.

## Conceitos demonstrados

- Uso de sockets TCP com `SOCK_STREAM`.
- Comunicação cliente-servidor.
- TCP como fluxo contínuo de bytes.
- Necessidade de delimitar mensagens no protocolo de aplicação.
- Leitura exata de bytes com `recv_exact`.
- Envio e recebimento de arquivos em blocos.
- Validação de integridade com SHA-256.
- Atendimento de múltiplos clientes com threads.

## Pontos de atenção

- O servidor salva os arquivos recebidos em `arquivos_recebidos/`.
- Arquivos com o mesmo nome substituem versões anteriores no destino final.
- O projeto é didático e não implementa autenticação, autorização ou criptografia.
- Para uso fora de ambiente local, considere adicionar TLS, autenticação e
  regras mais rígidas de permissão.
