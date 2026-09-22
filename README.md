# Fear & Greed Index — histórico diário

Site estático (HTML puro, sem build) que mostra o Fear & Greed Index da CNN
desde jan/2019, com um robô que atualiza os dados a cada hora.

## Arquivos

```
index.html                     → a página (lê data/data.json)
data/data.json                 → os dados (histórico + leitura atual)
scripts/update_data.py         → busca dados novos na CNN
.github/workflows/update.yml   → roda o script a cada hora
```

## Como publicar no GitHub Pages (5 minutos)

1. Crie um repositório novo no GitHub (pode ser público ou privado, mas
   GitHub Pages grátis só publica direto se for **público**, ou privado com
   plano pago).
2. Suba todos esses arquivos pra ele, mantendo a mesma estrutura de pastas
   (o `.github/workflows/update.yml` precisa continuar dentro de
   `.github/workflows/`).
3. No repositório, vá em **Settings → Pages**. Em "Source", escolha
   **Deploy from a branch**, selecione a branch `main` e a pasta `/ (root)`.
   Salve.
4. Espere 1-2 minutos. O GitHub mostra o link do site (algo como
   `https://seu-usuario.github.io/nome-do-repo/`).
5. Vá em **Settings → Actions → General**, e em "Workflow permissions"
   marque **Read and write permissions**. Isso é necessário pro robô
   conseguir salvar (`git push`) os dados novos.

Pronto. A partir daí:

- O workflow em `.github/workflows/update.yml` já está configurado pra
  rodar sozinho, todo minuto 5 de cada hora.
- Pra testar sem esperar a próxima hora cheia: vá na aba **Actions** do
  repositório, clique em "Atualizar Fear & Greed Index" na lista da
  esquerda, depois em **Run workflow** (botão à direita) → **Run workflow**.
  Em ~20-30 segundos o `data/data.json` é atualizado e commitado.

## Rodando localmente (opcional)

```bash
python3 scripts/update_data.py     # busca e grava data/data.json
python3 -m http.server 8000        # sobe um servidor local
# abra http://localhost:8000
```

## Notas

- **Frequência:** o cron está em `5 * * * *` (uma vez por hora). Dá pra
  mudar em `.github/workflows/update.yml` — por exemplo `*/15 * * * *`
  pra rodar a cada 15 minutos. O mínimo aceito pelo GitHub é a cada 5
  minutos, mas em repositórios gratuitos a execução pode atrasar em
  períodos de pico, então frequências muito curtas nem sempre são
  cumpridas à risca.
- **Se o workflow parar de rodar sozinho:** o GitHub desativa cron jobs
  em repositórios sem nenhuma atividade por 60 dias. Como o robô só
  commita quando o valor muda, em mercados fechados por muitos dias
  seguidos isso teoricamente poderia acontecer — mas rodar manualmente
  uma vez (Run workflow) reativa o agendamento.
- **Fonte dos dados:** `production.dataviz.cnn.io`, o mesmo endpoint que
  alimenta o gráfico oficial em `edition.cnn.com/markets/fear-and-greed`.
  Não é uma API pública documentada pela CNN — pode mudar de formato ou
  bloquear sem aviso. Se o robô começar a falhar, o `data/data.json`
  simplesmente para de crescer; o site continua funcionando com os
  últimos dados salvos.
