// =======================================================
// MSE TRAVEL EXPRESS — SISTEMA COMPLETO EM UM ARQUIVO
// Node.js + Express + Puppeteer + Google Maps API
// =======================================================

import express from "express";
import bodyParser from "body-parser";
import axios from "axios";
import puppeteer from "puppeteer";
import path from "path";
import { fileURLToPath } from "url";

// ==========================
// CONFIGURAÇÕES
// ==========================
const API_KEY = "SUA_API_KEY_GOOGLE";
const PRECO_KM = 0.50;

// ==========================
// AJUSTES DE PATH
// ==========================
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(bodyParser.json());
app.use(express.static("public"));

// ==========================
// MAPA DE CIDADES
// ==========================
const CIDADES_BR = {
  "londrina": "Londrina - PR",
  "curitiba": "Curitiba - PR",
  "maringa": "Maringá - PR",
  "foz do iguacu": "Foz do Iguaçu - PR",
  "sao paulo": "São Paulo - SP",
  "campinas": "Campinas - SP",
  "santos": "Santos - SP",
  "teresina": "Teresina - PI",
  "fortaleza": "Fortaleza - CE",
  "recife": "Recife - PE",
  "salvador": "Salvador - BA",
  "aracaju": "Aracaju - SE",
  "maceio": "Maceió - AL",
  "joao pessoa": "João Pessoa - PB",
  "natal": "Natal - RN",
  "belem": "Belém - PA",
  "macapa": "Macapá - AP",
  "palmas": "Palmas - TO",
  "porto alegre": "Porto Alegre - RS",
  "florianopolis": "Florianópolis - SC",
  "manaus": "Manaus - AM",
  "rio branco": "Rio Branco - AC",
  "boa vista": "Boa Vista - RR",
  "brasilia": "Brasília - DF",
  "goiania": "Goiânia - GO",
  "cuiaba": "Cuiabá - MT",
  "belo horizonte": "Belo Horizonte - MG",
  "bh": "Belo Horizonte - MG"
};

// =====================================================
// AJUSTAR CIDADE
// =====================================================
function ajustarCidade(cidade) {
  if (!cidade) return "";
  cidade = cidade.trim().toLowerCase();
  if (CIDADES_BR[cidade]) return CIDADES_BR[cidade];
  return cidade + ", Brasil";
}

// =====================================================
// GOOGLE MAPS — KM
// =====================================================
async function getKm(origem, destino) {
  origem = ajustarCidade(origem);
  destino = ajustarCidade(destino);

  const url =
    `https://maps.googleapis.com/maps/api/distancematrix/json?units=metric` +
    `&origins=${encodeURIComponent(origem)}` +
    `&destinations=${encodeURIComponent(destino)}` +
    `&key=${API_KEY}`;

  const res = await axios.get(url);
  const el = res.data.rows?.[0]?.elements?.[0];

  if (!el || el.status !== "OK") return 0;

  return el.distance.value / 1000;
}

// =====================================================
// CÁLCULO DE DIAS
// =====================================================
function calcularDias(ida, volta) {
  if (!ida || !volta) return 1;
  return Math.ceil((new Date(volta) - new Date(ida)) / 86400000);
}

// =====================================================
// VEÍCULOS
// =====================================================
const TABELA_DIARIA_VEICULO = {
  "B": 151.92,
  "EA": 203.44
};

async function cotarVeiculo(origem, destino, ida, volta, grupo) {
  const km = await getKm(origem, destino);
  const dias = calcularDias(ida, volta);
  const diaria = TABELA_DIARIA_VEICULO[grupo];

  const valorDiarias = diaria * dias;

  const precoCombustivel = 5.80;
  const consumo = (grupo === "B") ? 13 : 9;

  const kmTotal = km * 2;
  const litros = kmTotal / consumo;
  const valorCombustivel = litros * precoCombustivel;

  const total = valorDiarias + valorCombustivel;

  return `
      🚗 <b>Locação de Veículo</b><br><br>
      Dias: <b>${dias}</b><br>
      Diárias: <b>R$ ${valorDiarias.toFixed(2)}</b><br>
      Combustível: <b>R$ ${valorCombustivel.toFixed(2)}</b><br><br>
      <b>TOTAL: R$ ${total.toFixed(2)}</b>
    `;
}

// =====================================================
// HOSPEDAGEM
// =====================================================
const TABELA_HOSPEDAGEM = {
  "AC": 200, "AL": 200, "AP": 300, "AM": 350,
  "BA": 210, "CE": 350, "DF": 260, "ES": 300,
  "GO": 230, "MA": 260, "MT": 260, "MS": 260,
  "MG": 310, "PA": 300, "PB": 300, "PR": 250,
  "PE": 170, "PI": 160, "RJ": 305, "RN": 250,
  "RS": 280, "RO": 300, "RR": 300, "SC": 300,
  "SP": 350, "SE": 190, "TO": 270
};

function extrairUF(destino) {
  if (!destino.includes("-")) return null;
  return destino.split("-")[1].trim().toUpperCase();
}

function calcularDiasHosp(ida, volta) {
  return calcularDias(ida, volta) + 1;
}

async function cotarHospedagem(destino, ida, volta) {
  const uf = extrairUF(destino);

  if (!uf || !TABELA_HOSPEDAGEM[uf]) {
    return `
      ❌ <b>Destino inválido</b><br>
      Formato correto: Cidade - UF
    `;
  }

  const diaria = TABELA_HOSPEDAGEM[uf];
  const dias = calcularDiasHosp(ida, volta);
  const total = diaria * dias;

  return `
      🏨 <b>Hospedagem</b><br><br>
      UF: <b>${uf}</b><br>
      Dias: <b>${dias}</b><br>
      Total: <b>R$ ${total.toFixed(2)}</b><br>
    `;
}

// =====================================================
// RODOVIÁRIO
// =====================================================
async function cotarRodoviario(origem, destino) {
  const km = await getKm(origem, destino);
  const total = km * PRECO_KM;

  return `
      🚌 <b>Rodoviário</b><br><br>
      KM: <b>${km.toFixed(1)}</b><br>
      Total: <b>R$ ${total.toFixed(2)}</b>
    `;
}

// =====================================================
// COTAÇÃO GERAL
// =====================================================
async function cotarPortal(tipo, origem, destino, ida, volta, grupo) {
  if (tipo === "rodoviario") return await cotarRodoviario(origem, destino);
  if (tipo === "hospedagem") return await cotarHospedagem(destino, ida, volta);
  if (tipo === "veiculo") return await cotarVeiculo(origem, destino, ida, volta, grupo);

  const rod = await cotarRodoviario(origem, destino);
  const hosp = await cotarHospedagem(destino, ida, volta);
  const vei = await cotarVeiculo(origem, destino, ida, volta, grupo);

  return `
    <h2>📌 COTAÇÃO GERAL</h2><br>
    ${rod}<br><hr>
    ${hosp}<br><hr>
    ${vei}
  `;
}

// =====================================================
// PDF (Puppeteer)
// =====================================================
async function gerarPDF(html) {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();

  await page.setContent(`<html><body>${html}</body></html>`, {
    waitUntil: "load"
  });

  const filePath = path.join(__dirname, "public/Cotacao_MSE.pdf");

  await page.pdf({
    path: filePath,
    format: "A4",
    printBackground: true
  });

  await browser.close();
  return "/Cotacao_MSE.pdf";
}

// =====================================================
// ROTAS HTTP
// =====================================================
app.get("/", (req, res) => {
  res.send(`
    <h1>MSE Travel Express</h1>
    <p>API funcionando. Interface HTML deve estar em /public/index.html</p>
  `);
});

app.post("/cotar", async (req, res) => {
  const { tipo, origem, destino, ida, volta, grupo } = req.body;
  res.json({ html: await cotarPortal(tipo, origem, destino, ida, volta, grupo) });
});

app.post("/pdf", async (req, res) => {
  const { html } = req.body;
  const url = await gerarPDF(html);
  res.json({ url });
});

// =====================================================
// START SERVER
// =====================================================
const PORT = 3000;
app.listen(PORT, () => console.log(`🚀 MSE Travel Express rodando na porta ${PORT}`));
