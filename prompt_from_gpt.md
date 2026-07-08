You are a Principal Software Engineer and AI Agent Architect.

Your task is to build a production-ready Pokémon Product Monitoring Agent.

The code must be enterprise-grade.

The project will run inside Databricks as a scheduled Job every hour.

The objective is NOT to build a scraper.

The objective is to build a monitoring platform.

The code must be easily extensible for future Pokémon products.

#######################################################
TECH STACK
#######################################################

Python 3.12

Databricks

Delta Tables

Requests

BeautifulSoup

Playwright (when required)

Pydantic

PyYAML

Retry

Logging

OpenAI API (optional)

Slack Incoming Webhook

#######################################################
PROJECT STRUCTURE
#######################################################

pokemon_monitor/

config/

config.yaml

monitor/

crawler.py

website.py

parser.py

matcher.py

history.py

slack.py

classifier.py

scheduler.py

models/

product.py

offer.py

notification.py

storage/

delta.py

utils/

retry.py

cache.py

http.py

logger.py

main.py

#######################################################
MISSION
#######################################################

Monitor Pokémon products every hour.

The monitoring must be incremental.

Never notify twice for the same event.

Store history.

Track price evolution.

Track stock evolution.

Track newly created products.

#######################################################
PRODUCTS
#######################################################

Initially monitor only

Pokemon 30th Celebration

ETB

Elite Trainer Box

UPC

Ultra Premium Collection

Booster Bundle

Binder Collection

Figure Collection

Mew

Mewtwo

Pokemon Center Exclusive

#######################################################
COUNTRIES
#######################################################

France only.

#######################################################
WEBSITES
#######################################################

Priority A

Amazon France
(only seller Amazon)

Pokemon Center

Micromania

King Jouet

JouéClub

PicWicToys

Carrefour

Leclerc

Auchan

Cultura

Fnac

Priority B

Parkage

Ludifolie

DracauGames

Playin

Philibert

Ouvre Ton Booster

Le Temple du Jeu

UltraJeux

PokéStore

Pokélite

RelicTCG

Mana Source

Le Coin des Barons

BCD Jeux

Variantes

Troll2Jeux

L'Antre du Gobelin

The architecture must allow adding websites in less than 5 minutes.

#######################################################
DETECTION
#######################################################

Detect

new product

new preorder

price change

stock change

restock

new URL

new page

seller change

#######################################################
SMART FILTER
#######################################################

Ignore

Marketplace sellers

Scalpers

Out of stock

Price > configurable threshold

Products unrelated to Pokémon

#######################################################
PRICE ENGINE
#######################################################

Every product has

MSRP

Tolerance %

Maximum accepted price

Everything configurable.

#######################################################
DELTA TABLES
#######################################################

Create

pokemon_monitor.products

pokemon_monitor.price_history

pokemon_monitor.notifications

pokemon_monitor.errors

Store

website

product

url

price

availability

seller

first_seen

last_seen

hash

timestamp

#######################################################
AI
#######################################################

Use GPT ONLY when necessary.

Examples

Classify ambiguous products

Identify if a product belongs to Pokémon 30th Anniversary

Normalize titles

Detect duplicates

Never use GPT for scraping.

#######################################################
SLACK
#######################################################

Send notifications only for

New preorder

Price below threshold

Restock

Significant price drop (>10%)

New product discovered

Slack message example

🚨 Pokémon Hunter Alert

Website
Parkage

Product
30th Celebration ETB

Price
59.99 €

Status
Preorder Open

Reason
New preorder detected

Link
...

Group all products in one Slack message.

#######################################################
ROBUSTNESS
#######################################################

Retry

Timeout

Backoff

Rate limiting

User-Agent rotation

Gracefully continue on failures.

#######################################################
DISCOVERY
#######################################################

The agent must also detect pages that did not exist before.

Examples

New product page

New collection page

New category

#######################################################
QUALITY
#######################################################

Enterprise architecture.

SOLID principles.

Strong typing.

Unit-testable.

Reusable.

No duplicated code.

Generate production-ready code.

No pseudo code.

Ready to execute inside Databricks.