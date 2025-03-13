![](https://github.com/gongahkia/be-sure-ance/actions/workflows/scrape-to-supabase.yml/badge.svg)
![](https://api.netlify.com/api/v1/badges/281baeb4-46fd-4008-9f72-36324a3e1cad/deploy-status)
[![](https://img.shields.io/badge/be_sure_ance_1.0.0-passing-green)](https://github.com/gongahkia/be-sure-ance/releases/tag/1.0.0)

# `Be-sure-ance` 🤷‍♂️

Choosing and viewing insurance plans should be easy. 

## Usage

Use the live website [***here***](https://be-sure-ance.netlify.app/).

Sites are scraped weekly on [SGT Monday 12am](./.github/workflows/scrape-to-supabase.yml).

## Screenshots

<div style="display: flex; justify-content: space-between;">
  <img src="./../asset/1.png" width="48%">
  <img src="./../asset/2.png" width="48%">
</div>

<div style="display: flex; justify-content: space-between;">
  <img src="./../asset/3.png" width="48%">
  <img src="./../asset/4.png" width="48%">
</div>

## Architecture

### Stack

* [Frontend](./src/be-sure-ance-app/) - Vue.js, Netlify
* [Backend](./src/scrapers/) - Python, Github workflows
* [Database](./src/lib/create.sql) - Supabase

### Overview

```mermaid

```

### DB

```mermaid

```

## Legal disclaimer

...

## Details

`Be-sure-ance` supports the following Singaporean Insurance Providers. 

| Provider | Implementation Status | Implementation Date |
| :--- | :--- | :--- |
| [AIA Singapore Pte Ltd](https://www.aia.com.sg/en/index) | ✅ | 08/03/2025 |
| [Allianz Insurance (Singapore) Pte Ltd](https://www.allianz.sg/) | ❌ | | 
| [China Life Insurance (Singapore) Pte Ltd](https://www.chinalife.com.sg/) | ✅ | 12/03/2025 |
| [China Taiping Insurance (Singapore) Pte Ltd](https://www.sg.cntaiping.com/en/) | ❌ || 
| [Chubb Singapore Pte Ltd](https://www.chubb.com/sg-en/) | ✅ | 13/03/2025 | 
| [FWD Singapore Pte Ltd](https://www.fwd.com.sg/) | ❌ || 
| [Great Eastern Life Assurance Co Ltd](https://www.greateasternlife.com/sg/en/about-us.html) | ❌ | 08/03/2025 | 
| [HSBC Life (Singapore) Pte Ltd](https://www.insurance.hsbc.com.sg/) | ❌ || 
| [Manulife (Singapore) Pte Ltd](https://www.manulife.com.sg/) | ❌ || 
| [Prudential Assurance Company (Singapore) Pte Ltd](https://www.prudential.com.sg/) | ❌ || 
| [Raffles Health Insurance Pte Ltd](https://www.raffleshealthinsurance.com/) | ❌ || 
| [Singapore Life Ltd](https://singlife.com/en) | ✅ | 13/03/2025 | 
| [Sun Life Assurance Company of Canada Singapore Branch](https://www.sunlife.com.sg/en/) | ✅ | 13/03/2025 | 
| [Allied World Assurance Company Pte Ltd (Singapore)](https://alliedworldinsurance.com/singapore/) | ❌ || 
| [Auto & General Insurance (Singapore) Pte Ltd](https://www.aig.sg/home) | ❌ || 
| [ERGO Insurance Pte Ltd](https://www.ergo.com.sg/) | ❌ || 
| [Etiqa Insurance Pte Ltd](https://www.etiqa.com.sg/) | ❌ || 
| [HL Assurance Pte Ltd](https://www.hlas.com.sg/) | ❌ || 
| [Income Insurance Pte Ltd](https://www.income.com.sg/) | ❌ || 
| [India International Insurance Pte Ltd](https://www.iii.com.sg/) | ❌ || 
| [Liberty Insurance Pte Ltd](https://www.libertyinsurance.com.sg/) | ❌ || 
| [Lonpac Insurance Bhd](https://www.lonpac.com/) | ❌ || 
| [QBE Insurance (Singapore) Pte Ltd](https://www.qbe.com/sg) | ❌ || 
| [Sompo Insurance (Singapore) Pte Ltd](https://www.sompo.com.sg/) | ❌ || 
| [Tokio Marine Insurance (Singapore) Pte Ltd](https://www.tokiomarine.com/sg/en.html) | ✅ | 13/03/2025 | 
| [United Overseas Insurance Pte Ltd](https://www.uoi.com.sg/index.page) | ✅ | 08/03/2025 | 
| [Direct Asia Insurance (Singapore) Pte Ltd](https://www.directasia.com/) | ❌ || 
