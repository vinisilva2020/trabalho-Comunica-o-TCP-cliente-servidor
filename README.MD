# Trabalho de Redes 2

Implementação didática de comunicação TCP cliente-servidor em Python para
transferência de arquivos.

## Arquivos

- `servidor.py`: servidor TCP que recebe arquivos, valida o protocolo, confere
  o hash SHA-256 e salva em `arquivos_recebidos/`.
- `cliente.py`: cliente TCP que calcula o hash SHA-256 do arquivo, envia um
  cabeçalho binário e depois transmite o conteúdo em blocos.

## Como executar

Em um terminal, inicie o servidor:

```bash
python servidor.py
```

Em outro terminal, envie um arquivo:

```bash
python cliente.py 127.0.0.1 5000 caminho/do/arquivo.ext
```

## Protocolo da aplicação

O cliente envia primeiro um cabeçalho binário com o formato `!4sBHQ32s`:

- `4s`: identificador do protocolo, sempre `TRED`;
- `B`: versão do protocolo, atualmente `1`;
- `H`: tamanho do nome do arquivo;
- `Q`: tamanho do arquivo em bytes;
- `32s`: hash SHA-256 esperado do conteúdo.

Depois do cabeçalho, o cliente envia:

1. o nome do arquivo em UTF-8;
2. o conteúdo do arquivo como fluxo de bytes.

O servidor responde com:

- `status`: `0` para sucesso ou `1` para erro;
- `tamanho da mensagem`;
- `mensagem` em UTF-8.

## Conceitos demonstrados

- uso de sockets TCP com `SOCK_STREAM`;
- conexão cliente-servidor;
- TCP como fluxo de bytes;
- necessidade de delimitar dados no protocolo de aplicação;
- recebimento exato com `recv_exact`;
- confiabilidade e ordem garantidas pelo TCP;
- validação de integridade com SHA-256;
- atendimento de múltiplos clientes com threads.
