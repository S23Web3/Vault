# BingX API v3 Complete Reference

Scraped: 2026-02-27 10:44:00
Source: https://bingx-api.github.io/docs-v3/#/en/info
Total endpoints: 224

---

## Table of Contents

- [API DOCUMENT](#api-document)
- [BROKER](#broker)
- [API DOCUMENT(OLD)](#api-documentold)
  - [Introduce](#introduce)
  - [Quick Start](#quick-start)
    - [Signature Authentication](#signature-authentication)
    - [Basic Information](#basic-information)
    - [FAQ](#faq)
    - [WebSocket Rules](#websocket-rules)
      - [WebSocket Rules](#websocket-rules)
      - [Generate Listen Key](#generate-listen-key)
      - [Extend Listen Key Validity](#extend-listen-key-validity)
      - [Close Listen Key](#close-listen-key)
  - [Swap](#swap)
    - [Market Data](#market-data)
      - [USDT-M Perp Futures symbols](#usdt-m-perp-futures-symbols)
      - [Order Book](#order-book)
      - [Recent Trades List](#recent-trades-list)
      - [Mark Price and Funding Rate](#mark-price-and-funding-rate)
      - [Get Funding Rate History](#get-funding-rate-history)
      - [Kline/Candlestick Data](#klinecandlestick-data)
      - [Open Interest Statistics](#open-interest-statistics)
      - [24hr Ticker Price Change Statistics](#24hr-ticker-price-change-statistics)
      - [Query historical transaction orders](#query-historical-transaction-orders)
      - [Symbol Order Book Ticker](#symbol-order-book-ticker)
      - [Mark Price Kline/Candlestick Data](#mark-price-klinecandlestick-data)
      - [Symbol Price Ticker](#symbol-price-ticker)
      - [Trading Rules](#trading-rules)
    - [Trades Endpoints](#trades-endpoints)
      - [Test Order](#test-order)
      - [Place order](#place-order)
      - [Modify Order](#modify-order)
      - [Place multiple orders](#place-multiple-orders)
      - [Close All Positions](#close-all-positions)
      - [Cancel Order](#cancel-order)
      - [Cancel multiple orders](#cancel-multiple-orders)
      - [Cancel All Open Orders](#cancel-all-open-orders)
      - [Current All Open Orders](#current-all-open-orders)
      - [Query pending order status](#query-pending-order-status)
      - [Query Order details](#query-order-details)
      - [Query Margin Type](#query-margin-type)
      - [Change Margin Type](#change-margin-type)
      - [Query Leverage and Available Positions](#query-leverage-and-available-positions)
      - [Set Leverage](#set-leverage)
      - [User's Force Orders](#users-force-orders)
      - [Query Order history](#query-order-history)
      - [Modify Isolated Position Margin](#modify-isolated-position-margin)
      - [Query historical transaction orders](#query-historical-transaction-orders)
      - [Set Position Mode](#set-position-mode)
      - [Query position mode](#query-position-mode)
      - [Cancel an Existing Order and Send a New Orde](#cancel-an-existing-order-and-send-a-new-orde)
      - [Cancel orders in batches and place orders in batches](#cancel-orders-in-batches-and-place-orders-in-batches)
      - [Cancel All After](#cancel-all-after)
      - [Close position by position ID](#close-position-by-position-id)
      - [All Orders](#all-orders)
      - [Position and Maintenance Margin Ratio](#position-and-maintenance-margin-ratio)
      - [Query historical transaction details](#query-historical-transaction-details)
      - [Query Position History](#query-position-history)
      - [Isolated Margin Change History](#isolated-margin-change-history)
      - [Apply VST](#apply-vst)
      - [Place TWAP Order](#place-twap-order)
      - [Query TWAP Entrusted Order](#query-twap-entrusted-order)
      - [Query TWAP Historical Orders](#query-twap-historical-orders)
      - [TWAP Order Details](#twap-order-details)
      - [Cancel TWAP Order](#cancel-twap-order)
      - [Switch Multi-Assets Mode](#switch-multi-assets-mode)
      - [Query Multi-Assets Mode](#query-multi-assets-mode)
      - [Query Multi-Assets Rules](#query-multi-assets-rules)
      - [Query Multi-Assets Margin](#query-multi-assets-margin)
      - [One-Click Reverse Position](#one-click-reverse-position)
      - [Hedge mode Position - Automatic Margin Addition](#hedge-mode-position---automatic-margin-addition)
    - [Account Endpoints](#account-endpoints)
      - [Query account data](#query-account-data)
      - [Query position data](#query-position-data)
      - [Get Account Profit and Loss Fund Flow](#get-account-profit-and-loss-fund-flow)
      - [Export fund flow](#export-fund-flow)
      - [Query Trading Commission Rate](#query-trading-commission-rate)
    - [Websocket Market Data](#websocket-market-data)
      - [Partial Order Book Depth](#partial-order-book-depth)
      - [Subscribe the Latest Trade Detail](#subscribe-the-latest-trade-detail)
      - [Subscribe K-Line Data](#subscribe-k-line-data)
      - [Subscribe to 24-hour price changes](#subscribe-to-24-hour-price-changes)
      - [Subscribe to latest price changes](#subscribe-to-latest-price-changes)
      - [Subscribe to latest mark price changes](#subscribe-to-latest-mark-price-changes)
      - [Subscribe to the Book Ticker Streams](#subscribe-to-the-book-ticker-streams)
      - [Incremental Depth Information](#incremental-depth-information)
    - [Websocket Account Data](#websocket-account-data)
      - [Order update push](#order-update-push)
      - [Account balance and position update push](#account-balance-and-position-update-push)
      - [Configuration updates such as leverage and margin mode](#configuration-updates-such-as-leverage-and-margin-mode)
  - [Spot](#spot)
    - [Market Data](#market-data)
      - [Spot trading symbols](#spot-trading-symbols)
      - [Recent Trades List](#recent-trades-list)
      - [Order Book](#order-book)
      - [Kline/Candlestick Data](#klinecandlestick-data)
      - [24hr Ticker Price Change Statistics](#24hr-ticker-price-change-statistics)
      - [Order Book aggregation](#order-book-aggregation)
      - [Symbol Price Ticker](#symbol-price-ticker)
      - [Symbol Order Book Ticker](#symbol-order-book-ticker)
      - [Historical K-line](#historical-k-line)
      - [Old Trade Lookup](#old-trade-lookup)
    - [Account Endpoints](#account-endpoints)
      - [Query Assets](#query-assets)
      - [Asset transfer records](#asset-transfer-records)
      - [Main Accoun internal transfer](#main-accoun-internal-transfer)
      - [Asset Transfer New](#asset-transfer-new)
      - [Query transferable currency](#query-transferable-currency)
      - [Asset transfer records new](#asset-transfer-records-new)
      - [Query Fund Account Assets](#query-fund-account-assets)
      - [Main account internal transfer records](#main-account-internal-transfer-records)
      - [Asset overview](#asset-overview)
    - [Wallet deposits and withdrawals](#wallet-deposits-and-withdrawals)
      - [Deposit records](#deposit-records)
      - [Withdraw records](#withdraw-records)
      - [Query currency deposit and withdrawal data](#query-currency-deposit-and-withdrawal-data)
      - [Withdraw](#withdraw)
      - [Main Account Deposit Address](#main-account-deposit-address)
      - [Deposit risk control records](#deposit-risk-control-records)
    - [Trades Endpoints](#trades-endpoints)
      - [Place order](#place-order)
      - [Place multiple orders](#place-multiple-orders)
      - [Cancel Order](#cancel-order)
      - [Cancel multiple orders](#cancel-multiple-orders)
      - [Cancel all Open Orders on a Symbol](#cancel-all-open-orders-on-a-symbol)
      - [Cancel an Existing Order and Send a New Order](#cancel-an-existing-order-and-send-a-new-order)
      - [Query Order details](#query-order-details)
      - [Current Open Orders](#current-open-orders)
      - [Query Order history](#query-order-history)
      - [Query transaction details](#query-transaction-details)
      - [Query Trading Commission Rate](#query-trading-commission-rate)
      - [Cancel All After](#cancel-all-after)
      - [Create an OCO Order](#create-an-oco-order)
      - [Cancel an OCO Order List](#cancel-an-oco-order-list)
      - [Query an OCO Order List](#query-an-oco-order-list)
      - [Query All Open OCO Orders](#query-all-open-oco-orders)
      - [Query OCO Historical Order List](#query-oco-historical-order-list)
    - [Websocket Market Data](#websocket-market-data)
      - [Subscription transaction by transaction](#subscription-transaction-by-transaction)
      - [K-line Streamst](#k-line-streamst)
      - [Subscribe Market Depth Data](#subscribe-market-depth-data)
      - [Subscribe to 24-hour Price Change](#subscribe-to-24-hour-price-change)
      - [Spot Latest Trade Price](#spot-latest-trade-price)
      - [Spot Best Order Book](#spot-best-order-book)
      - [Incremental and Full Depth Information](#incremental-and-full-depth-information)
    - [Websocket Account Data](#websocket-account-data)
      - [order update event](#order-update-event)
      - [Subscription account balance push](#subscription-account-balance-push)
  - [Coin-M Futures](#coin-m-futures)
    - [Market Data](#market-data)
      - [Contract Information](#contract-information)
      - [Price & Current Funding Rate](#price-current-funding-rate)
      - [Get Swap Open Positions](#get-swap-open-positions)
      - [Get K-line Data](#get-k-line-data)
      - [Query Depth Data](#query-depth-data)
      - [Query 24-Hour Price Change](#query-24-hour-price-change)
    - [Trades Endpoints](#trades-endpoints)
      - [Trade order](#trade-order)
      - [Query Trade Commission Rate](#query-trade-commission-rate)
      - [Query Leverage](#query-leverage)
      - [Modify Leverage](#modify-leverage)
      - [Cancel all orders](#cancel-all-orders)
      - [Close all positions in bulk](#close-all-positions-in-bulk)
      - [Query warehouse](#query-warehouse)
      - [Query Account Assets](#query-account-assets)
      - [Query force orders](#query-force-orders)
      - [Query Order Trade Detail](#query-order-trade-detail)
      - [Cancel an Order](#cancel-an-order)
      - [Query all current pending orders](#query-all-current-pending-orders)
      - [Query Order](#query-order)
      - [User's History Orders](#users-history-orders)
      - [Query Margin Type](#query-margin-type)
      - [Set Margin Type](#set-margin-type)
      - [Adjust Isolated Margin](#adjust-isolated-margin)
    - [Websocket Market Data](#websocket-market-data)
      - [Subscription transaction by transaction](#subscription-transaction-by-transaction)
      - [Subscribe to the Latest Transaction Price](#subscribe-to-the-latest-transaction-price)
      - [Subscribe to Mark Price](#subscribe-to-mark-price)
      - [Subscribe to Limited Depth](#subscribe-to-limited-depth)
      - [Subscribe to Best Bid and Ask](#subscribe-to-best-bid-and-ask)
      - [Subscribe to Latest Trading Pair K-Line](#subscribe-to-latest-trading-pair-k-line)
      - [Subscribe to 24-Hour Price Change](#subscribe-to-24-hour-price-change)
    - [Websocket Account Data](#websocket-account-data)
      - [Account balance and position update push](#account-balance-and-position-update-push)
      - [Order update push](#order-update-push)
      - [Configuration updates such as leverage and margin mode](#configuration-updates-such-as-leverage-and-margin-mode)
  - [Account and Wallet](#account-and-wallet)
    - [Fund Account](#fund-account)
      - [Query Assets](#query-assets)
      - [Asset transfer records](#asset-transfer-records)
      - [Main Accoun internal transfer](#main-accoun-internal-transfer)
      - [Asset Transfer New](#asset-transfer-new)
      - [Query transferable currency](#query-transferable-currency)
      - [Asset transfer records new](#asset-transfer-records-new)
      - [Query Fund Account Assets](#query-fund-account-assets)
      - [Main account internal transfer records](#main-account-internal-transfer-records)
      - [Asset overview](#asset-overview)
    - [Wallet Deposits and Withdrawals](#wallet-deposits-and-withdrawals)
      - [Deposit records](#deposit-records)
      - [Withdraw records](#withdraw-records)
      - [Query currency deposit and withdrawal data](#query-currency-deposit-and-withdrawal-data)
      - [Withdraw](#withdraw)
      - [Main Account Deposit Address](#main-account-deposit-address)
      - [Deposit risk control records](#deposit-risk-control-records)
    - [Sub-account Management](#sub-account-management)
      - [Create Sub-account](#create-sub-account)
      - [Query API KEY Permissions](#query-api-key-permissions)
      - [Query Account UID](#query-account-uid)
      - [Query Sub-account List](#query-sub-account-list)
      - [Query Sub-account Asset Account](#query-sub-account-asset-account)
      - [Create Sub-account API Key](#create-sub-account-api-key)
      - [Query API Key Information](#query-api-key-information)
      - [Edit Sub-Account API Key](#edit-sub-account-api-key)
      - [Delete Sub-Account API Key](#delete-sub-account-api-key)
      - [Freeze/Unfreeze Sub-Account](#freezeunfreeze-sub-account)
      - [Authorize Sub-Account Internal Transfer](#authorize-sub-account-internal-transfer)
      - [Sub-account Internal Transfer](#sub-account-internal-transfer)
      - [Main Accoun internal transfer](#main-accoun-internal-transfer)
      - [Query Sub-account Deposit Address](#query-sub-account-deposit-address)
      - [Query Sub-account Deposit Address](#query-sub-account-deposit-address)
      - [Get Sub-account Deposit Records](#get-sub-account-deposit-records)
      - [Query Sub-account Internal Transfer Records](#query-sub-account-internal-transfer-records)
      - [Query Sub-Mother Account Transfer History](#query-sub-mother-account-transfer-history)
      - [Query Sub-Mother Account Transferable Amount](#query-sub-mother-account-transferable-amount)
      - [Sub-Mother Account Asset Transfer Interface](#sub-mother-account-asset-transfer-interface)
      - [Batch Query Sub-Account Asset Overview](#batch-query-sub-account-asset-overview)
  - [Agent](#agent)
    - [Query Invited Users](#query-invited-users)
    - [Daily commission details](#daily-commission-details)
    - [Query agent user information](#query-agent-user-information)
    - [Query the deposit details of invited users](#query-the-deposit-details-of-invited-users)
    - [Query API transaction commission （non-invitation relationship）](#query-api-transaction-commission-non-invitation-relationship)
    - [Query partner information](#query-partner-information)
    - [Invitation code data](#invitation-code-data)
    - [Superior verification](#superior-verification)
  - [Copy Trade](#copy-trade)
    - [USDT-M Perpetual Contracts](#usdt-m-perpetual-contracts)
      - [Trader’s current order](#traders-current-order)
      - [Traders close positions according to the order number](#traders-close-positions-according-to-the-order-number)
      - [Traders set take profit and stop loss based on order numbers](#traders-set-take-profit-and-stop-loss-based-on-order-numbers)
      - [Personal Trading Overview](#personal-trading-overview)
      - [Profit Overview](#profit-overview)
      - [Profit Details](#profit-details)
      - [Set Commission Rate](#set-commission-rate)
      - [Trader Gets Copy Trading Pairs](#trader-gets-copy-trading-pairs)
    - [Spot Trading](#spot-trading)
      - [Trader sells spot assets based on buy order number](#trader-sells-spot-assets-based-on-buy-order-number)
      - [Personal Trading Overview](#personal-trading-overview)
      - [Profit Summary](#profit-summary)
      - [Profit Details](#profit-details)
      - [Query Historical Orders](#query-historical-orders)
  - [CHANGE LOGS](#change-logs)

---

#### API DOCUMENT

Welcome to the BingXAPI.
You can use our API to access market data endpoints of spot trading. The market data API is publicly accessible and provides market data, statistics, order book depth of a Trading Pair.
If you have any questions or feedback, you can join the API issue Telegram group.
BingX sincerely invites you to participate in the API function user survey and share your ideas so that we can better serve you and enhance your trading experience.
Fill in the questionnaire

---

#### BROKER

Welcome to the BingXAPI.
You can use our API to access market data endpoints of spot trading. The market data API is publicly accessible and provides market data, statistics, order book depth of a Trading Pair.
If you have any questions or feedback, you can join the API issue Telegram group.
BingX sincerely invites you to participate in the API function user survey and share your ideas so that we can better serve you and enhance your trading experience.
Fill in the questionnaire

---

#### API DOCUMENT(OLD)

Welcome to the BingXAPI.
You can use our API to access market data endpoints of spot trading. The market data API is publicly accessible and provides market data, statistics, order book depth of a Trading Pair.
If you have any questions or feedback, you can join the API issue Telegram group.
BingX sincerely invites you to participate in the API function user survey and share your ideas so that we can better serve you and enhance your trading experience.
Fill in the questionnaire

---

#### Introduce

Welcome to the BingXAPI.
You can use our API to access market data endpoints of spot trading. The market data API is publicly accessible and provides market data, statistics, order book depth of a Trading Pair.
If you have any questions or feedback, you can join the API issue Telegram group.
BingX sincerely invites you to participate in the API function user survey and share your ideas so that we can better serve you and enhance your trading experience.
Fill in the questionnaire

---

### Quick Start

#### Signature Authentication

Signature Authentication
Generate an API Key
To access private endpoints, you must create an API Key on the BingX website under User Center → API Management.
After creation, you will receive an API Key and a Secret Key. Please keep them secure.
For security reasons, it is strongly recommended to configure an IP whitelist.
Never disclose your API Key or Secret Key. If leaked, delete it immediately and create a new one.
Permission Settings
Newly created API Keys have read-only permission by default.
To place orders or perform other write operations, please enable the corresponding permissions in the UI.
Request Requirements
All authenticated REST requests must include:
X-BX-APIKEY in the request header.
signature as a request parameter, calculated using the signature algorithm.
timestamp (milliseconds) as the request time. Requests outside the allowed time window (default 5000ms) will be rejected. The window can be adjusted using recvWindow.
Signature Description
The signature is generated using HMAC-SHA256 and returned as a 64-character lowercase hexadecimal string.
The signing and request construction rules are as follows:
1. Collect all business parameters (excluding signature).
2. Generate timestamp (milliseconds) and include it as a normal parameter.
3. Sort all parameters (business parameters + timestamp) by key in ASCII ascending order.
4. Build the signing string:
key=value&key2=value2&...×tamp=xxx
Parameter values must NOT be URL-encoded here.
5. Use secretKey to calculate HMAC-SHA256 over the signing string to obtain the signature.
URL Encoding Rules (Query String Only)
These rules apply only to query string parameters:
The signature is always calculated from the unencoded signing string.
If the signing string contains '[' or '{', URL-encode only parameter values in the actual request URL.
Do not encode parameter keys.
Use UTF-8 encoding and encode spaces as %20.
If the signing string does not contain '[' or '{', values do not need URL encoding.
Query String Example
Example parameters:
symbol=BTC-USDT
recvWindow=0
timestamp=1696751141337
Sorted signing string:
recvWindow=0&symbol=BTC-USDT×tamp=1696751141337
Generate signature:
echo -n 'recvWindow=0&symbol=BTC-USDT×tamp=1696751141337' | openssl dgst -sha256 -hmac 'SECRET_KEY' -hex
Send request:
https://open-api.bingx.com/xxx?recvWindow=0&symbol=BTC-USDT×tamp=1696751141337&signature=...
Batch Order Query String Example
Example request URL:
https://open-api.bingx.com/openApi/spot/v1/trade/batchOrders?data=%5B%7B%22symbol%22%3A%22BTC-USDT%22%2C%22side%22%3A%22BUY%22%2C%22type%22%3A%22LIMIT%22%2C%22quantity%22%3A0.001%2C%22price%22%3A85000%2C%22newClientOrderId%22%3A%22%22%7D%2C%7B%22symbol%22%3A%22BTC-USDT%22%2C%22side%22%3A%22BUY%22%2C%22type%22%3A%22LIMIT%22%2C%22quantity%22%3A0.001%2C%22price%22%3A42000%2C%22newClientOrderId%22%3A%22%22%7D%5D&recvWindow=60000×tamp=1766679008165&signature=87bd22cfb380dddf8ce6d2901be7f107fef23dcf1e3d066e1519d1daa8fa81c6
Request Body Example
The following example applies to endpoints that require application/json and read parameters from the request body.
Signature parameters (timestamp / signature) must be included in the request body. Do not append them to the URL query.
Example business parameters:
{
"recvWindow": 10000,
"symbol": "ETH-USDT",
"type": "MARKET",
"side": "SELL",
"positionSide": "SHORT",
"quantity": 0.01
}
Example request body:
{
"recvWindow": 10000,
"symbol": "ETH-USDT",
"type": "MARKET",
"side": "SELL",
"positionSide": "SHORT",
"quantity": 0.01,
"timestamp": 1696751141337,
"signature": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
Endpoints Using Request Body
The following endpoints use application/json format and send parameters via request body:
Create Sub-account - POST /openApi/subAccount/v1/create
Create Sub-account API Key - POST /openApi/subAccount/v1/apiKey/create
Edit Sub-Account API Key - POST /openApi/subAccount/v1/apiKey/edit
Delete Sub-Account API Key - POST /openApi/subAccount/v1/apiKey/del
Update Sub-account Status (Freeze/Unfreeze) - POST /openApi/subAccount/v1/updateStatus
Query Sub-Mother Account Transferable Amount - POST /openApi/account/transfer/v1/subAccount/transferAsset/supportCoins
Sub-Mother Account Asset Transfer - POST /openApi/account/transfer/v1/subAccount/transferAsset
Success
An HTTP 200 status code indicates a successful response. The response body, if present, will be returned in JSON format.

---

#### Basic Information

Common Error Codes
Common HTTP Error Codes
400 Bad Request – Invalid request format
401 Unauthorized – Invalid API Key
403 Forbidden – You do not have access to the requested resource
404 Not Found – Request not found
429 Too Many Requests – Requests are too frequent and are rate-limited by the system
418 – Received 429 and continued access, so the user is banned
500 Internal Server Error – Internal server error
504 – The server failed to get a response; further confirmation required
Common Business Error Codes
100202 - Balance is not enough to place batch orders
100400 - Invalid parameter
100404 - Order does not exist
100410 - Too many error requests in a short time, temporarily restricted
100421 - LIMIT pending orders reached the maximum limit (1000)
100441 - Account is abnormal, please contact customer service
100490 - Spot symbol is offline, please check symbol status
101202 - The value must be greater than the minimum allowed amount
101204 - Insufficient margin
101205 - No position to close
101209 - Maximum position value for this leverage has been reached
101212 - The available amount is insufficient
101222 - The current leverage poses high risks, please lower the leverage
101253 - Adjustable margin is insufficient
101400 - The minimum order amount requirement is not met
101402 - This account does not support trading of the trading pair
101484 - Advanced identity verification is required
101485 - The minimum size for closing an order is not met
104103 - Please close open positions or cancel pending orders first
109400 - Invalid parameters
109415 - Symbol is currently paused for trading
109420 - Position does not exist
109421 - Order does not exist
109425 - Symbol does not exist
109429 - Request is temporarily restricted due to risk control
109500 - User has pending orders or open positions
Timestamp Specifications
All timestamps in the API are returned in milliseconds.
The request timestamp must be within 5 seconds of the API server time, otherwise the request will be considered expired and rejected.
If there is a significant time discrepancy between the local server and the API server, it is recommended to use the API server time to update the HTTP header.
Example: 1587091154123
Numeric Specifications
To maintain precision across platforms, decimal numbers are returned as strings.
It is recommended to convert numbers into strings when making requests to avoid truncation and precision errors.
Integers (such as trade numbers and orders) are returned without quotation marks.
Rate Limiting
If requests are too frequent, the system will automatically rate-limit them and restore after 5 minutes.
Rate limiting is based on the account UID, with each API having its own independent rate limit.
Users can check the current rate-limiting status using 'X-RateLimit-Requests-Remain' (remaining requests) and 'X-RateLimit-Requests-Expire' (window expiration time) in the HTTP header.
Adjust the request frequency based on these values.
Query System Time
Request Method: GET
Endpoint: GET https://open-api.bingx.com/openApi/swap/v2/server/time
Return Parameters:
code - int64 - Error code, 0 means success, non-zero means failure
msg - string - Error message
serverTime - int64 - Current server time, in milliseconds
Sample Response:
{"code": 0, "msg": "", "data": {"serverTime": 1675319535362}}

---

#### FAQ

Q: Where are BingX servers located?
BingX is hosted on AWS in the Singapore region (ap-southeast-1), utilizing multiple Availability Zones, including Availability Zone IDs: apse1-az1, apse1-az2, and apse1-az3 to ensure high availability and stability.
Q: What is UID?
UID stands for User ID, which is a unique identifier for each user (including parent users and sub-users). UID can be viewed in the personal information section of the web or app interface, and it can also be obtained through the GET /openApi/account/v1/uid interface.
Q: How many API Keys can a user apply for?
Each parent user can create up to 20 sets of API Keys. Each parent user can also create up to 20 sub-users, and each sub-user can create up to 20 sets of API Keys. Each API Key can be set with different permissions.
Q: Why do I often experience disconnections and timeouts?
It could be due to network fluctuations. We recommend reconnecting in such cases.
Q: Why does WebSocket connection always get disconnected?
You can check if your code returns a Pong after receiving a Ping. If you are subscribing to account-related websockets, please also check if you are regularly updating the listenkey. We recommend using our sample code first.
Q: Why does signature authentication always fail?
Please carefully read our signature authentication instructions, or test using our sample code first.
Q: Is the API Key for U-based contracts the same as Spot trading?
The API Key for U-based contracts is the same as the API Key for Spot trading. However, the permissions for spot trading and contract trading are separate and need to be configured accordingly.
Q: How many types of risk control restrictions does BingX have for APIs?
BingX has three types of risk control strategies for APIs: api rate limiting, trading restrictions, and network firewall restrictions. These restrictions may change at any time.
Interface rate limiting: The rate limiting for each api may vary. Please refer to the specific api documentation for details.
Trading restrictions: Trading behavior is evaluated based on the behavior of regular users. If your trading behavior deviates significantly from that of regular users, you may be prohibited from trading, and the duration of the prohibition is uncertain. The duration of the trading prohibition may increase under the following circumstances:
1. Frequently occupying the best bid and ask prices.
2. Frequently placing/canceling orders without any trades.
3. Very low trade completion rate, where the completion rate = number of trades / (number of placed orders + number of canceled orders).
4. Very low trade weight, where the trade weight = total trade amount / (total placed order amount + total canceled order amount).
5. Continuously sending frequent requests after receiving a 429 error response.
Network Firewall Restrictions: Currently, we do not provide explicit information about network firewall restrictions. If you receive an HTTP 403 error message, it means you have violated a network firewall rule. In most cases, this error occurs due to excessive requests and will result in a five-minute temporary ban. However, if your requests are considered malicious, it may lead to a longer ban or even permanent suspension.
Q: How to report API errors?
Please contact our official customer service and provide the following template to report the issue. Our technical support will assist you:
1. Problem description
2. User ID (UID) and order ID (if related to account or order), API KEY
3. Complete request parameters (if applicable)
4. Complete JSON formatted response
5. Time and frequency of the issue (when it started, if it can be reproduced)
6. Signature information
Q: Does the API support standard contract trading?
Currently not supported.
Q: Does the API support stock and forex trading?
Currently not supported.
Q: Does the mobile app support API management?
This feature is under development.
Q: How many channels can be subscribed per IP address on BingX?
Currently, there is no limit, but there is a subscription rate limit. Please do not exceed 10/s.

---

#### WebSocket Rules

#### WebSocket Rules

Connection Limitations
A websocket is limited to a maximum of 200 topics, and 80403 error codes will be returned.
An IP limit is up to 60 websockets, beyond which the link will fail.
Access
The base URL of Live Websocket Market Data: wss://open-api-swap.bingx.com/swap-market
The base URL of VST Websocket Market Data: wss://vst-open-api-ws.bingx.com/swap-market
Data Compression
All response data from the Websocket server is compressed into GZIP format. Clients have to decompress them for further use.
Heartbeats
Once the Websocket Client and Websocket Server get connected, the server will send a heartbeat-Ping message every 5 seconds (the frequency might change).
When the Websocket Client receives this heartbeat message, it should return a Pong message.
Subscriptions
After successfully establishing a connection with the Websocket server, the Websocket client sends the following request to subscribe to a specific topic:
{ "id": "id1", "reqType": "sub", "dataType": "data to sub" }
After a successful subscription, the Websocket client will receive a confirmation message:
{ "id": "id1", "code": 0, "msg": "" }
After that, once the subscribed data is updated, the Websocket client will receive the update message pushed by the server.
Unsubscribe
The format of unsubscription is as follows:
{ "id": "id1", "reqType": "unsub", "dataType": "data to unsub" }
Confirmation of Unsubscription:
{ "id": "id1", "code": 0, "msg": "" }

---

#### Generate Listen Key

**GET** `/openApi/user/auth/userDataStream`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| filed | data type | description |  |

**Request Example**

```json
{}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "listenKey": "73a0914be44ce06d087ec2c97d4ec685e4cf26069a20900e2f4cd6694df9b734"
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/user/auth/userDataStream'
    method = "GET"
    paramsMap = {}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Extend Listen Key Validity

**PUT** `/openApi/user/auth/userDataStream`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| listenKey | string | Listen Key |  |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | error msg |  |

**Request Example**

```json
{
  "listenKey": "73a0914be44ce06d087ec2c97d4ec685e4cf26069a20900e2f4cd6694df9b734"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {}
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/user/auth/userDataStream'
    method = "PUT"
    paramsMap = {
    "listenKey": "73a0914be44ce06d087ec2c97d4ec685e4cf26069a20900e2f4cd6694df9b734"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Close Listen Key

**DELETE** `/openApi/user/auth/userDataStream`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| listenKey | string | Listen Key |  |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | error msg |  |

**Request Example**

```json
{
  "listenKey": "73a0914be44ce06d087ec2c97d4ec685e4cf26069a20900e2f4cd6694df9b734"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {}
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/user/auth/userDataStream'
    method = "DELETE"
    paramsMap = {
    "listenKey": "73a0914be44ce06d087ec2c97d4ec685e4cf26069a20900e2f4cd6694df9b734"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

### Swap

#### Market Data

#### USDT-M Perp Futures symbols

**GET** `/openApi/swap/v2/quote/contracts`

---

#### Order Book

**GET** `/openApi/swap/v2/quote/depth`

---

#### Recent Trades List

**GET** `/openApi/swap/v2/quote/trades`

---

#### Mark Price and Funding Rate

**GET** `/openApi/swap/v2/quote/premiumIndex`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| timestamp | int64 | Yes | Timestamp of initiating the request, Unit: milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | trading pair, for example: BTC-USDT |
| lastFundingRate | string | Last updated funding rate |
| markPrice | string | current mark price |
| indexPrice | string | index price |
| nextFundingTime | int64 | The remaining time for the next settlement, in milliseconds |

**Request Example**

```json
{
  "symbol": "BTC-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "symbol": "BTC-USDT",
    "markPrice": "42216.4",
    "indexPrice": "42219.9",
    "lastFundingRate": "0.00025100",
    "nextFundingTime": 1702742400000
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109425 | Trading pair does not exist |
| 100410 | rate limited |
| 109415 | Trading pair is suspended |
| 109400 | Invalid parameters |
| 109429 | Too many invalid requests |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/quote/premiumIndex'
    method = "GET"
    paramsMap = {
    "symbol": "BTC-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Get Funding Rate History

**GET** `/openApi/swap/v2/quote/fundingRate`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| startTime | int64 | No | Start time, unit: millisecond |
| endTime | int64 | No | End time, unit: millisecond |
| limit | int32 | No | default: 100 maximum: 1000 |
| timestamp | int64 | Yes | Timestamp of initiating the request, Unit: milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | trading pair, for example: BTC-USDT |
| fundingRate | string | funding rate |
| fundingTime | int64 | Funding time: milliseconds |

**Request Example**

```json
{
  "symbol": "QNT-USDT",
  "limit": 2
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": [
    {
      "symbol": "QNT-USDT",
      "fundingRate": "0.00027100",
      "fundingTime": 1702713600000
    },
    {
      "symbol": "QNT-USDT",
      "fundingRate": "0.00012800",
      "fundingTime": 1702684800000
    }
  ]
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109425 | Trading pair does not exist |
| 100410 | rate limited |
| 109400 | Invalid parameters |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/quote/fundingRate'
    method = "GET"
    paramsMap = {
    "symbol": "QNT-USDT",
    "limit": 2
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Kline/Candlestick Data

**GET** `/openApi/swap/v3/quote/klines`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| interval | string | Yes | time interval, refer to field description |
| startTime | int64 | No | Start time, unit: millisecond |
| endTime | int64 | No | End time, unit: millisecond |
| timeZone | int32 | No | Time zone offset, only supports 0 or 8 (UTC+0 or UTC+8) |
| limit | int64 | No | default: 500 maximum: 1440 |
| timestamp | int64 | Yes | Timestamp of initiating the request, Unit: milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| open | float64 | Opening Price |
| close | float64 | Closing Price |
| high | float64 | High Price |
| low | float64 | Low Price |
| volume | float64 | transaction volume |
| time | int64 | k-line time stamp, unit milliseconds |

**Request Example**

```json
{
  "symbol": "KNC-USDT",
  "interval": "1h",
  "timeZone": 8,
  "limit": "1000",
  "startTime": "1702717199998"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": [
    {
      "open": "0.7034",
      "close": "0.7065",
      "high": "0.7081",
      "low": "0.7033",
      "volume": "635494.00",
      "time": 1702717200000
    }
  ]
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109425 | Trading pair does not exist |
| 100410 | rate limited |
| 109415 | Trading pair is suspended |
| 109400 | Invalid parameters |
| 109429 | Too many invalid requests |
| 109419 | Trading pair not supported |
| 109701 | Network issue |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v3/quote/klines'
    method = "GET"
    paramsMap = {
    "symbol": "KNC-USDT",
    "interval": "1h",
    "timeZone": 8,
    "limit": "1000",
    "startTime": "1702717199998"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Open Interest Statistics

**GET** `/openApi/swap/v2/quote/openInterest`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| timestamp | int64 | Yes | Timestamp of initiating the request, Unit: milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| openInterest | string | Position Amount |
| symbol | string | contract name |
| time | int64 | matching engine time |

**Request Example**

```json
{
  "symbol": "EOS-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "openInterest": "7409966.52",
    "symbol": "EOS-USDT",
    "time": 1702719692859
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109425 | Trading pair does not exist |
| 109400 | OpenInterestNotExist |
| 109415 | Trading pair is suspended |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/quote/openInterest'
    method = "GET"
    paramsMap = {
    "symbol": "EOS-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### 24hr Ticker Price Change Statistics

**GET** `/openApi/swap/v2/quote/ticker`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| timestamp | int64 | Yes | Timestamp of initiating the request, Unit: milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | trading pair, for example: BTC-USDT |
| priceChange | string | 24 hour price change |
| priceChangePercent | string | price change percentage |
| lastPrice | string | latest transaction price |
| lastQty | string | latest transaction amount |
| highPrice | string | 24-hour highest price |
| lowPrice | string | 24 hours lowest price |
| volume | string | 24-hour volume |
| quoteVolume | string | 24-hour turnover, the unit is USDT |
| openPrice | string | first price within 24 hours |
| openTime | int64 | The time when the first transaction occurred within 24 hours |
| closeTime | int64 | The time when the last transaction occurred within 24 hours |
| bidPrice | float64 | bid price |
| bidQty | float64 | bid quantity |
| askPrice | float64 | ask price |
| askQty | float64 | ask quantity |

**Request Example**

```json
{
  "symbol": "SFP-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "symbol": "SFP-USDT",
    "priceChange": "0.0295",
    "priceChangePercent": "4.15",
    "lastPrice": "0.7409",
    "lastQty": "10",
    "highPrice": "0.7506",
    "lowPrice": "0.6903",
    "volume": "4308212",
    "quoteVolume": "3085449.53",
    "openPrice": "0.7114",
    "openTime": 1702719833853,
    "closeTime": 1702719798603,
    "askPrice": "0.7414",
    "askQty": "99",
    "bidPrice": "0.7413",
    "bidQty": "84"
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109425 | Trading pair does not exist |
| 100410 | rate limited |
| 109400 | Invalid parameters |
| 109415 | Trading pair is suspended |
| 109429 | Too many invalid requests |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/quote/ticker'
    method = "GET"
    paramsMap = {
    "symbol": "SFP-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query historical transaction orders

**GET** `/openApi/swap/v1/market/historicalTrades`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| fromId | int64 | No | From which transaction ID to start returning. By default, it returns the most recent transaction records |
| symbol | string | No | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| limit | int64 | No | The number of returned result sets The default value is 50, the maximum value is 100 |
| timestamp | int64 | Yes | request timestamp, unit: millisecond |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| time | int64 | transaction time |
| isBuyerMaker | bool | Whether the buyer is the maker of the order (true / false) |
| price | string | transaction price |
| qty | string | transaction quantity |
| quoteQty | string | turnover |
| id | string | transaction ID |

**Request Example**

```json
{
  "fromId": "412551",
  "limit": "500",
  "symbol": "ETH-USDT",
  "recvWindow": "60000"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": [
    {
      "time": 1705063108365,
      "isBuyerMaker": true,
      "price": "2662.83",
      "qty": "0.10",
      "quoteQty": "266.28",
      "id": "8179911"
    },
    {
      "time": 1705063108486,
      "isBuyerMaker": true,
      "price": "2662.82",
      "qty": "0.10",
      "quoteQty": "266.28",
      "id": "8179912"
    }
  ]
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109400 | timestamp is invalid |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/market/historicalTrades'
    method = "GET"
    paramsMap = {
    "fromId": "412551",
    "limit": "500",
    "symbol": "ETH-USDT",
    "recvWindow": "60000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Symbol Order Book Ticker

**GET** `/openApi/swap/v2/quote/bookTicker`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| timestamp | int64 | Yes | Timestamp of initiating the request, Unit: milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| bid_price | float64 | Optimal purchase price |
| bid_qty | float64 | Order quantity |
| ask_price | float64 | Best selling price |
| lastUpdateId | int64 | The ID of the latest trade |
| time | long | The time of the trade in milliseconds |
| ask_qty | float64 | Order quantity |

**Request Example**

```json
{
  "symbol": "BTC-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "book_ticker": {
      "symbol": "BTC-USDT",
      "bid_price": 42211.1,
      "bid_qty": 12663,
      "ask_price": 42211.8,
      "ask_qty": 128854
    }
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109425 | Trading pair does not exist |
| 109400 | Invalid parameters |
| 109415 | Trading pair is suspended |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/quote/bookTicker'
    method = "GET"
    paramsMap = {
    "symbol": "BTC-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Mark Price Kline/Candlestick Data

**GET** `/openApi/swap/v1/market/markPriceKlines`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| interval | string | Yes | time interval, refer to field description |
| startTime | int64 | No | Start time, unit: millisecond |
| endTime | int64 | No | End time, unit: millisecond |
| limit | int64 | No | default: 500 maximum: 1440 |
| timestamp | int64 | Yes | Timestamp of initiating the request, Unit: milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| open | float64 | Opening Price |
| close | float64 | Closing Price |
| high | float64 | High Price |
| low | float64 | Low Price |
| openTime | int64 | transaction volume |
| closeTime | int64 | k-line time stamp, unit milliseconds |

**Request Example**

```json
{
  "symbol": "KNC-USDT",
  "interval": "1h",
  "limit": "1000",
  "startTime": "1702717199998"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": [
    {
      "open": "0.7034",
      "close": "0.7065",
      "high": "0.7081",
      "low": "0.7033",
      "volume": "635494.00",
      "openTime": 1705820520000,
      "closeTime": 1705820520000
    }
  ]
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109425 | Trading pair does not exist |
| 109415 | Trading pair is suspended |
| 109701 | Network issue |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/market/markPriceKlines'
    method = "GET"
    paramsMap = {
    "symbol": "KNC-USDT",
    "interval": "1h",
    "limit": "1000",
    "startTime": "1702717199998"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Symbol Price Ticker

**GET** `/openApi/swap/v1/ticker/price`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT,If no transaction pair parameters are sent, all transaction pair information will be returned |
| timestamp | int64 | Yes | Timestamp of initiating the request, Unit: milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | trading pair, for example: BTC-USDT |
| price | string | price |
| time | int64 | matching engine time |

**Request Example**

```json
{
  "symbol": "TIA-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "symbol": "TIA-USDT",
    "price": "14.0658",
    "time": 1702718922941
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109425 | Trading pair does not exist |
| 109400 | Invalid parameters |
| 109415 | Trading pair is suspended |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/ticker/price'
    method = "GET"
    paramsMap = {
    "symbol": "TIA-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Trading Rules

**GET** `/openApi/swap/v1/tradingRules`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | Trading pair, e.g. BTC-USDT. Please use uppercase letters. If not provided, information for all trading pairs will be returned. |
| timestamp | int64 | Yes | Current timestamp in milliseconds. Required for request signature validation; must match the current system time. |
| recvWindow | int64 | No | Request validity window value in milliseconds. |

**Response Body**

| filed | data type | description |
|---|---|---|
| minSizeCoin | string | Minimum order quantity, denominated in coin. |
| minSizeUsd | string | Minimum order amount, denominated in USDT. |
| maxMumOrder | string | Maximum number of open orders for this contract, including: limit orders, market orders, stop orders, trailing orders, take-profit orders, stop-loss orders, and OCO orders. |
| protectionThreshold | string | Spread protection threshold (decimal). If spread protection is enabled and when a strategy order is triggered, if the spread between the latest price and mark price exceeds this threshold, the order will fail. |
| buyMaxPrice | string | Upper limit ratio for limit order buy price (decimal). Limit order price must satisfy: current price × lower limit < order price < current price × upper limit. |
| buyMinPrice | string | Lower limit ratio for limit order buy price (decimal). Limit order price must satisfy: current price × lower limit < order price < current price × upper limit. |
| sellMaxPrice | string | Upper limit ratio for limit order sell price (decimal). Limit order price must satisfy: current price × lower limit < order price < current price × upper limit. |
| sellMinPrice | string | Lower limit ratio for limit order sell price (decimal). Limit order price must satisfy: current price × lower limit < order price < current price × upper limit. |
| marketRatio | string | Price tolerance ratio for market orders (decimal). If the spread between the market order execution price and mark price exceeds this ratio, the order may fail or be partially filled. |

**Request Example**

```json
{
  "symbol": "BTC-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "timestamp": 1756711590730,
  "data": {
    "minSizeCoin": "0.0001",
    "minSizeUsd": "2.00",
    "maxNumOrder": "200",
    "protectionThreshold": "0.05",
    "buyMaxPrice": "1.1",
    "buyMinPrice": "0.2",
    "sellMaxPrice": "5",
    "sellMinPrice": "0.9",
    "marketRatio": "0.08"
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109400 | Contract does not exist |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/tradingRules'
    method = "GET"
    paramsMap = {
    "symbol": "BTC-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Trades Endpoints

#### Test Order

**POST** `/openApi/swap/v2/trade/order/test`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| type | string | Yes | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order / TRAILING_TP_SL: Trailing TakeProfit or StopLoss |
| side | string | Yes | buying and selling direction SELL, BUY |
| positionSide | string | No | Position direction, required for single position as BOTH, for both long and short positions only LONG or SHORT can be chosen, defaults to LONG if empty |
| reduceOnly | string | No | true, false; Default value is false for single position mode; This parameter is not accepted for both long and short positions mode |
| price | float64 | No | Price, represents the trailing stop distance in TRAILING_STOP_MARKET and TRAILING_TP_SL |
| quantity | float64 | No | Original quantity, only support units by COIN ,Ordering with quantity U is not currently supported. |
| stopPrice | float64 | No | Trigger price, only required for STOP_MARKET, TAKE_PROFIT_MARKET, STOP, TAKE_PROFIT, TRIGGER_LIMIT, TRIGGER_MARKET |
| priceRate | float64 | No | For type: TRAILING_STOP_MARKET or TRAILING_TP_SL; Maximum: 1 |
| timestamp | int64 | Yes | request timestamp, unit: millisecond |
| stopLoss | string | No | Support setting stop loss while placing an order. Only supports type: STOP_MARKET/STOP |
| takeProfit | string | No | Support setting take profit while placing an order. Only supports type: TAKE_PROFIT_MARKET/TAKE_PROFIT |
| clientOrderId | string | No | Customized order ID for users, with a limit of characters from 1 to 40. Different orders cannot use the same clientOrderId |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |
| timeInForce | string | No | Time in Force, currently supports PostOnly, GTC, IOC, and FOK |
| closePosition | string | No | true, false; all position squaring after triggering, only support STOP_MARKET and TAKE_PROFIT_MARKET; not used with quantity; comes with only position squaring effect, not used with reduceOnly |
| activationPrice | float64 | No | Used with TRAILING_STOP_MARKET or TRAILING_TP_SL orders, default as the latest price(supporting different workingType) |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | trading pair, for example: BTC-USDT |
| side | string | buying and selling direction |
| type | string | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order / TRAILING_TP_SL: Trailing TakeProfit or StopLoss |
| positionSide | string | Position direction, required for single position as BOTH, for both long and short positions only LONG or SHORT can be chosen, defaults to LONG if empty |
| reduceOnly | string | true, false; Default value is false for single position mode; This parameter is not accepted for both long and short positions mode |
| orderId | int64 | Order ID |
| clientOrderId | string | Customized order ID for users |

**Request Example**

```json
{
  "symbol": "BTC-USDT",
  "side": "BUY",
  "positionSide": "LONG",
  "type": "MARKET",
  "quantity": 5,
  "takeProfit": "{\"type\": \"TAKE_PROFIT_MARKET\", \"stopPrice\": 31968.0,\"price\": 31968.0,\"workingType\":\"MARK_PRICE\"}"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "order": {
      "symbol": "BTC-USDT",
      "orderId": 1735950529123455000,
      "side": "BUY",
      "positionSide": "LONG",
      "type": "MARKET",
      "clientOrderId": "",
      "workingType": "MARK_PRICE"
    }
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 100001 | Signature verification failed |
| 100413 | Incorrect API key |
| 100004 | Permission denied |
| 109400 | Invalid parameters |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/order/test'
    method = "POST"
    paramsMap = {
    "symbol": "BTC-USDT",
    "side": "BUY",
    "positionSide": "LONG",
    "type": "MARKET",
    "quantity": 5,
    "takeProfit": "{\"type\": \"TAKE_PROFIT_MARKET\", \"stopPrice\": 31968.0,\"price\": 31968.0,\"workingType\":\"MARK_PRICE\"}"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Place order

**POST** `/openApi/swap/v2/trade/order`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| type | string | Yes | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order / TRAILING_TP_SL: Trailing TakeProfit or StopLoss |
| side | string | Yes | buying and selling direction SELL, BUY |
| positionSide | string | No | Position direction, required for single position as BOTH, for both long and short positions only LONG or SHORT can be chosen, defaults to LONG if empty |
| reduceOnly | string | No | true, false; Default value is false for single position mode; This parameter is not accepted for both long and short positions mode |
| price | float64 | No | Price, represents the trailing stop distance in TRAILING_STOP_MARKET and TRAILING_TP_SL |
| quantity | float64 | No | Original quantity, only support units by COIN ,Ordering with quantity U is not currently supported. |
| quoteOrderQty | float64 | No | Quote order quantity, e.g., 100USDT,if quantity and quoteOrderQty are input at the same time, quantity will be used first, and quoteOrderQty will be discarded |
| stopPrice | float64 | No | Trigger price, only required for STOP_MARKET, TAKE_PROFIT_MARKET, STOP, TAKE_PROFIT, TRIGGER_LIMIT, TRIGGER_MARKET |
| priceRate | float64 | No | For type: TRAILING_STOP_MARKET or TRAILING_TP_SL; Maximum: 1 |
| workingType | string | No | The stopPrice trigger price type can be MARK_PRICE, CONTRACT_PRICE, or INDEX_PRICE, with the default set to MARK_PRICE. When the order type is STOP or STOP_MARKET and stopGuaranteed = true, the workingType can only be set to CONTRACT_PRICE. |
| timestamp | int64 | Yes | Support setting take profit while placing an order. Only supports type: TAKE_PROFIT_MARKET/TAKE_PROFIT |
| stopLoss | string | No | StopPrice trigger price types: MARK_PRICE, CONTRACT_PRICE, INDEX_PRICE, default MARK_PRICE. When the type is STOP or STOP_MARKET, and stopGuaranteed is true, the workingType must only be CONTRACT_PRICE. |
| takeProfit | string | No | request timestamp, unit: millisecond |
| clientOrderId | string | No | Customized order ID for users, with a limit of characters from 1 to 40. The system will convert this field to lowercase. Different orders cannot use the same clientOrderId, clientOrderId only supports LIMIT/MARKET order type |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |
| timeInForce | string | No | Time in Force, currently supports PostOnly, GTC, IOC, and FOK |
| closePosition | string | No | true, false; all position squaring after triggering, only support STOP_MARKET and TAKE_PROFIT_MARKET; not used with quantity; comes with only position squaring effect, not used with reduceOnly |
| activationPrice | float64 | No | Used with TRAILING_STOP_MARKET or TRAILING_TP_SL orders, default as the latest price(supporting different workingType) |
| stopGuaranteed | string | No | true: Enables the guaranteed stop-loss and take-profit feature; false: Disables the feature; cutfee: Enable the guaranteed stop loss function and enable the VIP guaranteed stop loss fee reduction function. When stopGuaranteed is true or cutfee, the quantity field does not take effect. The guaranteed stop-loss feature is not enabled by default. Supported order types include: STOP_MARKET: Market stop-loss order / TAKE_PROFIT_MARKET: Market take-profit order / STOP: Limit stop-loss order / TAKE_PROFIT: Limit take-profit order / TRIGGER_LIMIT: Stop-limit order with trigger / TRIGGER_MARKET: Market order with trigger for stop-loss. |
| positionId | int64 | No | In the Separate Isolated mode, closing a position must be transmitted |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | trading pair, for example: BTC-USDT |
| side | string | buying and selling direction |
| type | string | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order / TRAILING_TP_SL: Trailing TakeProfit or StopLoss |
| positionSide | string | Position direction, required for single position as BOTH, for both long and short positions only LONG or SHORT can be chosen, defaults to LONG if empty |
| reduceOnly | string | true, false; Default value is false for single position mode; This parameter is not accepted for both long and short positions mode |
| orderID | string | Order ID |
| workingType | string | StopPrice trigger price types: MARK_PRICE, CONTRACT_PRICE, INDEX_PRICE, default MARK_PRICE. When the type is STOP or STOP_MARKET, and stopGuaranteed is true, the workingType must only be CONTRACT_PRICE. |
| clientOrderId | string | Customized order ID for users. The system will convert this field to lowercase. |
| stopGuaranteed | string | true: Enables the guaranteed stop-loss and take-profit feature; false: Disables the feature; cutfee: Enable the guaranteed stop loss function and enable the VIP guaranteed stop loss fee reduction function. The VIP fee reduction only takes effect when placing a stop loss order.. The guaranteed stop-loss feature is not enabled by default. Supported order types include: STOP_MARKET: Market stop-loss order / TAKE_PROFIT_MARKET: Market take-profit order / STOP: Limit stop-loss order / TAKE_PROFIT: Limit take-profit order / TRIGGER_LIMIT: Stop-limit order with trigger / TRIGGER_MARKET: Market order with trigger for stop-loss. |
| status | string | Order status |
| avgPrice | string | Average filled price, present when type=MARKET |
| executedQty | string | Transaction quantity, coins |

**Request Example**

```json
[
  {
    "title": "MARKET",
    "desc": "Place an order at market price and set a take profit",
    "payload": {
      "symbol": "BTC-USDT",
      "side": "BUY",
      "positionSide": "LONG",
      "type": "MARKET",
      "quantity": 5,
      "takeProfit": "{\"type\": \"TAKE_PROFIT_MARKET\", \"stopPrice\": 31968.0,\"price\": 31968.0,\"workingType\":\"MARK_PRICE\"}"
    }
  },
  {
    "title": "STOP_MARKET",
    "desc": "Market stop loss order",
    "payload": {
      "type": "STOP_MARKET",
      "stopPrice": 50000,
      "symbol": "BTC-USDT",
      "side": "SELL",
      "quantity": 0.002,
      "positionSide": "LONG",
      "clientOrderID": "",
      "recvWindow": 1000,
      "timeInForce": "GTC",
      "workingType": "",
      "timestamp": 1726223068783
    }
  },
  {
    "title": "TAKE_PROFIT_MARKET",
    "desc": "Market price take profit order",
    "payload": {
      "type": "TAKE_PROFIT_MARKET",
      "stopPrice": 70000,
      "symbol": "BTC-USDT",
      "side": "SELL",
      "quantity": 0.002,
      "positionSide": "LONG",
      "clientOrderID": "",
      "recvWindow": 1000,
      "timeInForce": "GTC",
      "workingType": "",
      "timestamp": 1726223068783
    }
  },
  {
    "title": "STOP",
    "desc": "Stop limit order",
    "payload": {
      "type": "STOP",
      "price": 50000,
      "stopPrice": 50000,
      "priceRate": 0,
      "symbol": "BTC-USDT",
      "side": "SELL",
      "quantity": 0.002,
      "positionSide": "LONG",
      "clientOrderID": "",
      "recvWindow": 1000,
      "timeInForce": "GTC",
      "workingType": "",
      "timestamp": 1726223068783
    }
  },
  {
    "title": "TAKE_PROFIT",
    "desc": "Limit price and take profit order",
    "payload": {
      "type": "TAKE_PROFIT",
      "price": 70000,
      "stopPrice": 70000,
      "priceRate": 0,
      "symbol": "BTC-USDT",
      "side": "SELL",
      "quantity": 0.002,
      "positionSide": "LONG",
      "clientOrderID": "",
      "recvWindow": 1000,
      "timeInForce": "GTC",
      "workingType": "",
      "timestamp": 1726223068783
    }
  },
  {
    "title": "TRIGGER_LIMIT",
    "desc": "Limit order with trigger",
    "payload": {
      "type": "TRIGGER_LIMIT",
      "price": 70000,
      "stopPrice": 70000,
      "priceRate": 0,
      "symbol": "BTC-USDT",
      "side": "BUY",
      "quantity": 0.002,
      "positionSide": "LONG",
      "clientOrderID": "",
      "takeProfit": "",
      "recvWindow": 1000,
      "stopLoss": "",
      "timeInForce": "GTC",
      "workingType": "",
      "timestamp": 1726223068783
    }
  },
  {
    "title": "TRIGGER_MARKET",
    "desc": "Market order with trigger",
    "payload": {
      "type": "TRIGGER_MARKET",
      "stopPrice": 70000,
      "symbol": "BTC-USDT",
      "side": "BUY",
      "quantity": 0.002,
      "positionSide": "LONG",
      "clientOrderID": "",
      "takeProfit": "",
      "recvWindow": 1000,
      "stopLoss": "",
      "timeInForce": "GTC",
      "workingType": "",
      "timestamp": 1726223068783
    }
  },
  {
    "title": "TRAILING_STOP_MARKET",
    "desc": "Trailing Stop Market Order",
    "payload": {
      "type": "TRAILING_STOP_MARKET",
      "price": 0,
      "stopPrice": 0,
      "priceRate": 0.1,
      "symbol": "BTC-USDT",
      "side": "BUY",
      "quantity": 0.002,
      "positionSide": "LONG",
      "clientOrderID": "",
      "recvWindow": 1000,
      "timeInForce": "GTC",
      "workingType": "",
      "timestamp": 1726223068783
    }
  },
  {
    "title": "TRAILING_TP_SL",
    "desc": "Trailing TakeProfit or StopLoss",
    "payload": {
      "type": "TRAILING_TP_SL",
      "price": 0,
      "stopPrice": 0,
      "priceRate": 0.1,
      "symbol": "BTC-USDT",
      "side": "SELL",
      "quantity": 0.002,
      "positionSide": "LONG",
      "clientOrderID": "",
      "recvWindow": 1000,
      "timeInForce": "GTC",
      "workingType": "",
      "timestamp": 1726231037325
    }
  },
  {
    "title": "POSITION_STOP_MARKET",
    "desc": "Market price position stop loss order",
    "payload": {
      "type": "STOP_MARKET",
      "closePosition": true,
      "stopPrice": 50000,
      "symbol": "BTC-USDT",
      "side": "SELL",
      "quantity": 0.002,
      "positionSide": "LONG",
      "clientOrderID": "",
      "recvWindow": 1000,
      "timeInForce": "GTC",
      "workingType": "",
      "timestamp": 1726223068783
    }
  },
  {
    "title": "POSITION_TAKE_PROFIT_MARKET",
    "desc": "Market price position take profit order",
    "payload": {
      "type": "TAKE_PROFIT_MARKET",
      "closePosition": true,
      "stopPrice": 70000,
      "symbol": "BTC-USDT",
      "side": "SELL",
      "quantity": 0.002,
      "positionSide": "LONG",
      "clientOrderID": "",
      "recvWindow": 1000,
      "timeInForce": "GTC",
      "workingType": "",
      "timestamp": 1726223068783
    }
  }
]
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "order": {
      "symbol": "BTC-USDT",
      "orderId": 1735950529123455000,
      "side": "BUY",
      "positionSide": "LONG",
      "type": "MARKET",
      "clientOrderId": "",
      "workingType": "MARK_PRICE"
    }
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 101204 | Insufficient margin |
| 109400 | timestamp is invalid |
| 101205 | No position to close |
| 109429 | Too many repeated errors |
| 101253 | Insufficient margin |
| 101400 | clientOrderID unique check failed |
| 110424 | Order size exceeds available amount |
| 109425 | Trading pair does not exist |
| 101212 | Available amount is insufficient |
| 101485 | Order size below minimum |
| 100004 | Permission denied |
| 101209 | Maximum position value reached |
| 101222 | Leverage risk too high |
| 100413 | Incorrect API key |
| 109420 | Position not exist |
| 101484 | Advanced verification required |
| 110411 | Invalid Stop Loss price |
| 100410 | Rate limited |
| 100001 | Signature verification failed |
| 110413 | Invalid Take Profit price |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/order'
    method = "POST"
    paramsMap = {
    "symbol": "BTC-USDT",
    "side": "BUY",
    "positionSide": "LONG",
    "type": "MARKET",
    "quantity": 5,
    "takeProfit": "{\"type\": \"TAKE_PROFIT_MARKET\", \"stopPrice\": 31968.0,\"price\": 31968.0,\"workingType\":\"MARK_PRICE\"}"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Modify Order

**POST** `/openApi/swap/v1/trade/amend`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| orderId | string | Yes | Either orderId or clientOrderId must be provided. At least one of them is required. |
| clientOrderId | string | Yes | Either orderId or clientOrderId must be provided. At least one of them is required. |
| quantity | float | Yes | The amended order quantity. |
| symbol | string | Yes | Trading pair, e.g., BTC-USDT (please use uppercase letters). |
| recvWindow | int64 | No | Request validity window, in milliseconds. |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int64 | Error code: 0 means success; any non-zero value indicates a failure. |
| msg | string | Error message. |
| orderId | int64 | Order ID. |
| clientOrderId | string | Client order ID (if applicable). |
| symbol | string | Trading pair, e.g., BTC-USDT (please use uppercase letters). |
| quantity | float | The amended order quantity. |

**Request Example**

```json
{
  "orderId": "1989246372640980993",
  "quantity": 0.00009,
  "symbol": "BTC-USDT",
  "recvWindow": "10000"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "orderId": 1989246372640981000,
    "clientOrderId": "",
    "symbol": "BTC-USDT",
    "quantity": 0.00009
  },
  "timestamp": 0
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109400 | Invalid parameters |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/trade/amend'
    method = "POST"
    paramsMap = {
    "orderId": "1989246372640980993",
    "quantity": 0.00009,
    "symbol": "BTC-USDT",
    "recvWindow": "10000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Place multiple orders

**POST** `/openApi/swap/v2/trade/batchOrders`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| batchOrders | LIST<Order> | Yes | Order list, supporting up to 5 orders, with Order objects referencing transactions to place orders |
| timestamp | int64 | Yes | request timestamp, unit: millisecond |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | trading pair, for example: BTC-USDT |
| side | string | buying and selling direction |
| type | string | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order / TRAILING_TP_SL: Trailing TakeProfit or StopLoss |
| positionSide | string | Position direction, required for single position as BOTH, for both long and short positions only LONG or SHORT can be chosen, defaults to LONG if empty |
| reduceOnly | string | true, false; Default value is false for single position mode; This parameter is not accepted for both long and short positions mode |
| orderID | string | Order ID |
| workingType | string | Customized order ID for users. The system will convert this field to lowercase. |
| clientOrderId | string | true: Enables the guaranteed stop-loss and take-profit feature; false: Disables the feature. The guaranteed stop-loss feature is not enabled by default. Supported order types include: STOP_MARKET: Market stop-loss order / TAKE_PROFIT_MARKET: Market take-profit order / STOP: Limit stop-loss order / TAKE_PROFIT: Limit take-profit order / TRIGGER_LIMIT: Stop-limit order with trigger / TRIGGER_MARKET: Market order with trigger for stop-loss. |
| stopGuaranteed | string | Order status |
| status | string | Average filled price, present when type=MARKET |
| avgPrice | string | Transaction quantity, coins |

**Request Example**

```json
{
  "batchOrders": "[{\"symbol\": \"ETH-USDT\",\"type\": \"MARKET\",\"side\": \"BUY\",\"positionSide\": \"LONG\",\"quantity\": 1},{\"symbol\": \"BTC-USDT\",\"type\": \"MARKET\",\"side\": \"BUY\",\"positionSide\": \"LONG\",\"quantity\": 0.001}]"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "orders": [
      {
        "symbol": "ID-USDT",
        "orderId": 1736010300483712300,
        "side": "SELL",
        "positionSide": "LONG",
        "type": "MARKET",
        "clientOrderId": "",
        "workingType": ""
      }
    ]
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109403 | Risk forbidden |
| 112414 | Total position amount reached platform limit |
| 101400 | Order amount below minimum |
| 109500 | Invalid symbol format |
| 100500 | System busy |
| 110420 | Invalid TP/SL or activation price |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/batchOrders'
    method = "POST"
    paramsMap = {
    "batchOrders": "[{\"symbol\": \"ETH-USDT\",\"type\": \"MARKET\",\"side\": \"BUY\",\"positionSide\": \"LONG\",\"quantity\": 1},{\"symbol\": \"BTC-USDT\",\"type\": \"MARKET\",\"side\": \"BUY\",\"positionSide\": \"LONG\",\"quantity\": 0.001}]"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Close All Positions

**POST** `/openApi/swap/v2/trade/closeAllPositions`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | Trading pair, for example: BTC-USDT, please use capital letters. |
| timestamp | int64 | Yes | request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| success | LIST<int64> | Multiple order numbers generated by all one-click liquidation |
| failed | 結构數組 | the order number of the failed position closing |

**Request Example**

```json
{
  "symbol": "BTC-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "success": [
      1736008778921491200
    ],
    "failed": null
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 100419 | IP whitelist mismatch |
| 109400 | timestamp is invalid |
| 100410 | rate limited |
| 109403 | risk forbidden |
| 100400 | Gateway timeout |
| 100413 | Incorrect apiKey |
| 100004 | Permission denied (missing trading permission) |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/closeAllPositions'
    method = "POST"
    paramsMap = {
    "symbol": "BTC-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Cancel Order

**DELETE** `/openApi/swap/v2/trade/order`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| orderId | int64 | No | Order ID |
| clientOrderId | string | No | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| symbol | string | Yes | Customized order ID for users, with a limit of characters from 1 to 40. The system will convert this field to lowercase. Different orders cannot use the same clientOrderId |
| timestamp | int64 | Yes | request timestamp, unit: millisecond |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| time | int64 | order time, unit: millisecond |
| symbol | string | trading pair, for example: BTC-USDT |
| side | string | buying and selling direction |
| type | string | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order |
| positionSide | string | position side |
| cumQuote | string | transaction amount |
| status | string | order status |
| stopPrice | string | Trigger price |
| price | string | Price |
| origQty | string | original order quantity |
| avgPrice | string | average transaction price |
| executedQty | string | volume |
| orderId | int64 | Order ID |
| profit | string | profit and loss |
| commission | string | Fee |
| updateTime | int64 | update time, unit: millisecond |
| clientOrderId | string | Customized order ID for users. The system will convert this field to lowercase. |

**Request Example**

```json
{
  "orderId": "1736011869418901234",
  "symbol": "RNDR-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "order": {
      "symbol": "RNDR-USDT",
      "orderId": 1736011869418901200,
      "side": "BUY",
      "positionSide": "LONG",
      "type": "LIMIT",
      "origQty": "3",
      "price": "4.5081",
      "executedQty": "0",
      "avgPrice": "0.0000",
      "cumQuote": "0",
      "stopPrice": "",
      "profit": "0.0000",
      "commission": "0.000000",
      "status": "CANCELLED",
      "time": 1702732457867,
      "updateTime": 1702732457888,
      "clientOrderId": "lo******7",
      "leverage": "",
      "takeProfit": {
        "type": "",
        "quantity": 0,
        "stopPrice": 0,
        "price": 0,
        "workingType": ""
      },
      "stopLoss": {
        "type": "",
        "quantity": 0,
        "stopPrice": 0,
        "price": 0,
        "workingType": ""
      },
      "advanceAttr": 0,
      "positionID": 0,
      "takeProfitEntrustPrice": 0,
      "stopLossEntrustPrice": 0,
      "orderType": "",
      "workingType": ""
    }
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109201 | The same order number is only allowed to be submitted once within 1 second. |
| 80018 | order is already filled, The order doesn't exist |
| 80018 | order is already filled, The order doesn't exist |
| 80001 | service has some errors, The order doesn't exist |
| 109414 | order not exist |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/order'
    method = "DELETE"
    paramsMap = {
    "orderId": "1736011869418901234",
    "symbol": "RNDR-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Cancel multiple orders

**DELETE** `/openApi/swap/v2/trade/batchOrders`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| orderIdList | LIST<int64> | No | system order number, up to 10 orders [1234567,2345678] |
| clientOrderIdList | LIST<string> | No | Customized order ID for users, up to 10 orders ["abc1234567","abc2345678"]. The system will convert this field to lowercase. |
| symbol | string | Yes | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| timestamp | int64 | Yes | request timestamp, unit: millisecond |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int64 | error code, 0 means successfully response, others means response failure |
| msg | string | Error Details Description |
| success | LIST<Order> | list of successfully canceled orders |
| failed | 結构數組 | list of failed orders |
| orderId | int64 | Order ID |
| errorCode | int64 | error code, 0 means successfully response, others means response failure |
| errorMessage | string | Error Details Description |

**Request Example**

```json
{
  "orderIdList": "[1735924831603391122, 1735924833239172233]",
  "symbol": "BTC-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "success": [
      {
        "symbol": "BTC-USDT",
        "orderId": 1735924831603391200,
        "side": "BUY",
        "positionSide": "LONG",
        "type": "LIMIT",
        "origQty": "0.0032",
        "price": "41682.9",
        "executedQty": "0.0000",
        "avgPrice": "0.0",
        "cumQuote": "0",
        "stopPrice": "",
        "profit": "0.0000",
        "commission": "0.000000",
        "status": "CANCELLED",
        "time": 1702711706435,
        "updateTime": 1702711706453,
        "clientOrderId": "",
        "leverage": "",
        "takeProfit": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": ""
        },
        "stopLoss": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": ""
        },
        "advanceAttr": 0,
        "positionID": 0,
        "takeProfitEntrustPrice": 0,
        "stopLossEntrustPrice": 0,
        "orderType": "",
        "workingType": ""
      },
      {
        "symbol": "BTC-USDT",
        "orderId": 1735924833239172400,
        "side": "BUY",
        "positionSide": "LONG",
        "type": "LIMIT",
        "origQty": "0.0033",
        "price": "41182.9",
        "executedQty": "0.0000",
        "avgPrice": "0.0",
        "cumQuote": "0",
        "stopPrice": "",
        "profit": "0.0000",
        "commission": "0.000000",
        "status": "CANCELLED",
        "time": 1702711706825,
        "updateTime": 1702711706838,
        "clientOrderId": "",
        "leverage": "",
        "takeProfit": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": ""
        },
        "stopLoss": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": ""
        },
        "advanceAttr": 0,
        "positionID": 0,
        "takeProfitEntrustPrice": 0,
        "stopLossEntrustPrice": 0,
        "orderType": "",
        "workingType": ""
      }
    ],
    "failed": null
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 80014 | orderIdList & clientOrderIDList are both empty; |
| 109201 | The same order number is only allowed to be submitted once within 1 second. |
| 109201 | The same order number is only allowed to be submitted once within 1 second. |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/batchOrders'
    method = "DELETE"
    paramsMap = {
    "orderIdList": "[1735924831603391122, 1735924833239172233]",
    "symbol": "BTC-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Cancel All Open Orders

**DELETE** `/openApi/swap/v2/trade/allOpenOrders`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT,if you do not fill this field,will delete all type of orders |
| type | string | No | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order / TRAILING_TP_SL: Trailing TakeProfit or StopLoss |
| timestamp | int64 | Yes | request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| success | LIST<Order> | list of successfully canceled orders |
| failed | LIST<FailOrder> | list of failed orders |

**Request Example**

```json
{
  "recvWindow": "0",
  "symbol": "ATOM-USDT",
  "type": "LIMIT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "success": [
      {
        "symbol": "ATOM-USDT",
        "orderId": 1736013373487123500,
        "side": "SELL",
        "positionSide": "SHORT",
        "type": "LIMIT",
        "origQty": "3.00",
        "price": "13.044",
        "executedQty": "0.00",
        "avgPrice": "0.000",
        "cumQuote": "0",
        "stopPrice": "",
        "profit": "0",
        "commission": "0",
        "status": "CANCELLED",
        "time": 1702732816465,
        "updateTime": 1702732816488,
        "clientOrderId": "",
        "leverage": "",
        "takeProfit": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": ""
        },
        "stopLoss": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": ""
        },
        "advanceAttr": 0,
        "positionID": 0,
        "takeProfitEntrustPrice": 0,
        "stopLossEntrustPrice": 0,
        "orderType": "",
        "workingType": ""
      },
      {
        "symbol": "ATOM-USDT",
        "orderId": 1736013373487123500,
        "side": "BUY",
        "positionSide": "SHORT",
        "type": "LIMIT",
        "origQty": "3.00",
        "price": "11.292",
        "executedQty": "0.00",
        "avgPrice": "0.000",
        "cumQuote": "0",
        "stopPrice": "",
        "profit": "0",
        "commission": "0",
        "status": "CANCELLED",
        "time": 1702732816820,
        "updateTime": 1702732816839,
        "clientOrderId": "",
        "leverage": "",
        "takeProfit": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": ""
        },
        "stopLoss": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": ""
        },
        "advanceAttr": 0,
        "positionID": 0,
        "takeProfitEntrustPrice": 0,
        "stopLossEntrustPrice": 0,
        "orderType": "",
        "workingType": ""
      }
    ],
    "failed": [
      {
        "orderId": 111111,
        "clientOrderId": "111111",
        "errorCode": 80012,
        "errorMessage": "cancel order failed"
      },
      {
        "orderId": 222222,
        "clientOrderId": "222222",
        "errorCode": 80012,
        "errorMessage": "cancel order failed"
      }
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/allOpenOrders'
    method = "DELETE"
    paramsMap = {
    "recvWindow": "0",
    "symbol": "ATOM-USDT",
    "type": "LIMIT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Current All Open Orders

**GET** `/openApi/swap/v2/trade/openOrders`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT,When not filled, query all pending orders. When filled, query the pending orders for the corresponding currency pair |
| type | string | No | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order / TRAILING_TP_SL: Trailing TakeProfit or StopLoss |
| timestamp | int64 | Yes | request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| time | int64 | order time, unit: millisecond |
| symbol | string | trading pair, for example: BTC-USDT |
| side | string | buying and selling direction |
| type | string | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order/ TRIGGER_REVERSE_MARKET: trigger reverse Market order / TRAILING_TP_SL: trailing take Profit or stop loss |
| positionSide | string | Position direction, required for single position as BOTH, for both long and short positions only LONG or SHORT can be chosen, defaults to LONG if empty |
| reduceOnly | string | true, false; Default value is false for single position mode; This parameter is not accepted for both long and short positions mode |
| cumQuote | string | transaction amount |
| status | string | order status |
| stopPrice | string | Trigger price |
| price | string | Price. When the type is TRAILING_STOP_MARKET or TRAILING_TP_SL, this field represents the trailing distance. |
| origQty | string | original order quantity |
| avgPrice | string | average transaction price |
| executedQty | string | volume |
| orderId | int64 | Order ID |
| profit | string | profit and loss |
| commission | string | Fee |
| workingType | string | StopPrice trigger price types: MARK_PRICE, CONTRACT_PRICE, INDEX_PRICE, default MARK_PRICE |
| updateTime | int64 | update time, unit: millisecond |
| postOnly | bool | Maker only |
| trailingStopRate | float64 | Retracement rate |
| trailingStopDistance | int64 | trailing distance |
| stopGuaranteed | string | true: Enables the guaranteed stop-loss and take-profit feature; false: Disables the feature. The guaranteed stop-loss feature is not enabled by default. Supported order types include: STOP_MARKET: Market stop-loss order / TAKE_PROFIT_MARKET: Market take-profit order / STOP: Limit stop-loss order / TAKE_PROFIT: Limit take-profit order / TRIGGER_LIMIT: Stop-limit order with trigger / TRIGGER_MARKET: Market order with trigger for stop-loss. |
| priceRate | string | This field has a value only when the type is TRAILING_STOP_MARKET or TRAILING_TP_SL, and the priceRate is provided in the order; otherwise, it is an empty string. |
| actPrice | string | Activation price, used only for TRAILING_STOP_MARKET or TRAILING_TP_SL orders |
| closePosition | string | Whether to close the entire position |

**Request Example**

```json
{
  "symbol": "BTC-USDT",
  "type": "LIMIT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "orders": [
      {
        "symbol": "BTC-USDT",
        "orderId": 1733405587011123500,
        "side": "SELL",
        "positionSide": "LONG",
        "type": "LIMIT",
        "origQty": "0.0030",
        "price": "44459.6",
        "executedQty": "0.0000",
        "avgPrice": "0.0",
        "cumQuote": "0",
        "stopPrice": "",
        "profit": "0.0",
        "commission": "0.0",
        "status": "PENDING",
        "time": 1702256915574,
        "updateTime": 1702256915610,
        "clientOrderId": "",
        "leverage": "",
        "takeProfit": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": "",
          "StopGuaranteed": ""
        },
        "stopLoss": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": "",
          "StopGuaranteed": ""
        },
        "advanceAttr": 0,
        "positionID": 0,
        "takeProfitEntrustPrice": 0,
        "stopLossEntrustPrice": 0,
        "orderType": "",
        "trailingStopRate": 0,
        "trailingStopDistance": 0,
        "postOnly": false,
        "workingType": "MARK_PRICE"
      },
      {
        "symbol": "BTC-USDT",
        "orderId": 1733405587011123500,
        "side": "SELL",
        "positionSide": "LONG",
        "type": "LIMIT",
        "origQty": "0.0030",
        "price": "44454.6",
        "executedQty": "0.0000",
        "avgPrice": "0.0",
        "cumQuote": "0",
        "stopPrice": "",
        "profit": "0.0",
        "commission": "0.0",
        "status": "PENDING",
        "time": 1702111071719,
        "updateTime": 1702111071735,
        "clientOrderId": "",
        "leverage": "",
        "takeProfit": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": "",
          "StopGuaranteed": ""
        },
        "stopLoss": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": "",
          "StopGuaranteed": ""
        },
        "advanceAttr": 0,
        "positionID": 0,
        "takeProfitEntrustPrice": 0,
        "stopLossEntrustPrice": 0,
        "orderType": "",
        "trailingStopRate": 0,
        "trailingStopDistance": 0,
        "postOnly": false,
        "workingType": "MARK_PRICE"
      }
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/openOrders'
    method = "GET"
    paramsMap = {
    "symbol": "BTC-USDT",
    "type": "LIMIT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query pending order status

**GET** `/openApi/swap/v2/trade/openOrder`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| orderId | int64 | No | Order ID |
| clientOrderId | string | No | Customized order ID for users, with a limit of characters from 1 to 40. Different orders cannot use the same clientOrderId |
| timestamp | int64 | Yes | request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| time | int64 | order time, unit: millisecond |
| symbol | string | trading pair, for example: BTC-USDT |
| side | string | buying and selling direction |
| type | string | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order |
| positionSide | string | Position direction, required for single position as BOTH, for both long and short positions only LONG or SHORT can be chosen, defaults to LONG if empty |
| reduceOnly | string | true, false; Default value is false for single position mode; This parameter is not accepted for both long and short positions mode |
| cumQuote | string | transaction amount |
| status | string | order status |
| stopPrice | string | Trigger price |
| price | string | Price |
| origQty | string | original order quantity |
| avgPrice | string | average transaction price |
| executedQty | string | volume |
| orderId | int64 | Order ID |
| profit | string | profit and loss |
| commission | string | Fee |
| updateTime | int64 | update time, unit: millisecond |
| clientOrderId | string | StopPrice trigger price types: MARK_PRICE, CONTRACT_PRICE, INDEX_PRICE, default MARK_PRICE |
| workingType | string | Customized order ID for users |

**Request Example**

```json
{
  "orderId": "1736012449498123456",
  "symbol": "OP-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "order": {
      "symbol": "OP-USDT",
      "orderId": 1736012449498123500,
      "side": "SELL",
      "positionSide": "LONG",
      "type": "LIMIT",
      "origQty": "1.0",
      "price": "2.1710",
      "executedQty": "0.0",
      "avgPrice": "0.0000",
      "cumQuote": "0",
      "stopPrice": "",
      "profit": "0.0000",
      "commission": "0.000000",
      "status": "PENDING",
      "time": 1702732596168,
      "updateTime": 1702732596188,
      "clientOrderId": "l*****e",
      "leverage": "",
      "takeProfit": {
        "type": "",
        "quantity": 0,
        "stopPrice": 0,
        "price": 0,
        "workingType": ""
      },
      "stopLoss": {
        "type": "",
        "quantity": 0,
        "stopPrice": 0,
        "price": 0,
        "workingType": ""
      },
      "advanceAttr": 0,
      "positionID": 0,
      "takeProfitEntrustPrice": 0,
      "stopLossEntrustPrice": 0,
      "orderType": "",
      "workingType": "MARK_PRICE"
    }
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 80016 | order does not exist |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/openOrder'
    method = "GET"
    paramsMap = {
    "orderId": "1736012449498123456",
    "symbol": "OP-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Order details

**GET** `/openApi/swap/v2/trade/order`

- **Rate Limit**: UID Rate Limit 30/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| orderId | int64 | No | Order ID |
| clientOrderId | string | No | Customized order ID for users, with a limit of characters from 1 to 40. The system will convert this field to lowercase. Different orders cannot use the same clientOrderId |
| timestamp | int64 | Yes | request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| time | int64 | order time, unit: millisecond |
| symbol | string | trading pair, for example: BTC-USDT |
| side | string | buying and selling direction |
| type | string | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order |
| positionSide | string | Position direction, required for single position as BOTH, for both long and short positions only LONG or SHORT can be chosen, defaults to LONG if empty |
| reduceOnly | string | true, false; Default value is false for single position mode; This parameter is not accepted for both long and short positions mode |
| cumQuote | string | transaction amount |
| status | string | order status |
| stopPrice | string | Trigger price |
| price | string | Price |
| origQty | string | original order quantity |
| avgPrice | string | average transaction price |
| executedQty | string | volume |
| orderId | int64 | Order ID |
| profit | string | profit and loss |
| commission | string | Fee |
| updateTime | int64 | update time, unit: millisecond |
| clientOrderId | string | StopPrice trigger price types: MARK_PRICE, CONTRACT_PRICE, INDEX_PRICE, default MARK_PRICE |
| workingType | string | Customized order ID for users. The system will convert this field to lowercase. |
| stopGuaranteed | string | true: Enables the guaranteed stop-loss and take-profit feature; false: Disables the feature. The guaranteed stop-loss feature is not enabled by default. Supported order types include: STOP_MARKET: Market stop-loss order / TAKE_PROFIT_MARKET: Market take-profit order / STOP: Limit stop-loss order / TAKE_PROFIT: Limit take-profit order / TRIGGER_LIMIT: Stop-limit order with trigger / TRIGGER_MARKET: Market order with trigger for stop-loss. |
| triggerOrderId | int64 | trigger order ID associated with this order |
| closePosition | string | Whether to close the entire position |

**Request Example**

```json
{
  "orderId": "1736012449498123456",
  "symbol": "OP-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "order": {
      "symbol": "OP-USDT",
      "orderId": 1736012449498123500,
      "side": "SELL",
      "positionSide": "LONG",
      "type": "LIMIT",
      "origQty": "1.0",
      "price": "2.1710",
      "executedQty": "0.0",
      "avgPrice": "0.0000",
      "cumQuote": "0",
      "stopPrice": "",
      "profit": "0.0000",
      "commission": "0.000000",
      "status": "PENDING",
      "time": 1702732596168,
      "updateTime": 1702732596188,
      "clientOrderId": "l*****e",
      "leverage": "",
      "takeProfit": {
        "type": "",
        "quantity": 0,
        "stopPrice": 0,
        "price": 0,
        "workingType": ""
      },
      "stopLoss": {
        "type": "",
        "quantity": 0,
        "stopPrice": 0,
        "price": 0,
        "workingType": ""
      },
      "advanceAttr": 0,
      "positionID": 0,
      "takeProfitEntrustPrice": 0,
      "stopLossEntrustPrice": 0,
      "orderType": "",
      "workingType": "MARK_PRICE",
      "stopGuaranteed": false,
      "triggerOrderId": 1736012449498123500
    }
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 80016 | order does not exist |
| 109414 | Request failed |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/order'
    method = "GET"
    paramsMap = {
    "orderId": "1736012449498123456",
    "symbol": "OP-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Margin Type

**GET** `/openApi/swap/v2/trade/marginType`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| timestamp | int64 | Yes | request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| marginType | string | margin mode |

**Request Example**

```json
{
  "symbol": "WOO-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "marginType": "CROSSED"
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/marginType'
    method = "GET"
    paramsMap = {
    "symbol": "WOO-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Change Margin Type

**POST** `/openApi/swap/v2/trade/marginType`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| timestamp | int64 | Yes | request timestamp in milliseconds |
| marginType | string | Yes | Margin mode ISOLATED (isolated margin), CROSSED (cross margin) and SEPARATE_ISOLATED (separated isolated margin) |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int64 | error code, 0 means successfully response, others means response failure |
| msg | string | Error Details Description |

**Request Example**

```json
{
  "symbol": "MINA-USDT",
  "marginType": "CROSSED",
  "recvWindow": "60000"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": ""
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109400 | the account has positions or pending orders |
| 109500 | SetTradingStrategy network failed |
| 80012 | query Service Unavailable, err:contract not exist |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/marginType'
    method = "POST"
    paramsMap = {
    "symbol": "MINA-USDT",
    "marginType": "CROSSED",
    "recvWindow": "60000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Leverage and Available Positions

**GET** `/openApi/swap/v2/trade/leverage`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| timestamp | int64 | Yes | request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| longLeverage | int64 | Long position leverage |
| shortLeverage | int64 | Short position Leverage |
| maxLongLeverage | int64 | Max Long position leverage |
| maxShortLeverage | int64 | Max Short position Leverage |
| availableLongVol | string | Available Long Volume |
| availableShortVol | string | Available Short Volume |
| availableLongVal | string | Available Long Value |
| availableShortVal | string | Available Short Value |
| maxPositionLongVal | string | Maximum Position Long Value |
| maxPositionShortVal | string | Maximum Position Short Value |

**Request Example**

```json
{
  "symbol": "BCH-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "longLeverage": 50,
    "shortLeverage": 50,
    "maxLongLeverage": 75,
    "maxShortLeverage": 75
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109500 | Account Service Unavailable, err:symbol not exist |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/leverage'
    method = "GET"
    paramsMap = {
    "symbol": "BCH-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Set Leverage

**POST** `/openApi/swap/v2/trade/leverage`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| side | string | Yes | Leverage for long or short positions. In the Hedge mode, LONG for long positions, SHORT for short positions. In the One-way mode, only supports BOTH. |
| timestamp | int64 | Yes | request timestamp in milliseconds |
| leverage | int64 | Yes | leverage |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| leverage | int64 | leverage |
| symbol | string | trading pair |
| availableLongVol | string | Available Long Volume |
| availableShortVol | string | Available Short Volume |
| availableLongVal | string | Available Long Value |
| availableShortVal | string | Available Short Value |
| maxPositionLongVal | string | Maximum Position Long Value |
| maxPositionShortVal | string | Maximum Position Short Value |

**Request Example**

```json
{
  "leverage": "8",
  "side": "SHORT",
  "symbol": "ETH-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "leverage": 8,
    "symbol": "ETH-USDT"
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109400 | margin is not enough |
| 109400 | In the Hedge mode, the 'Side' field can only be set to LONG or SHORT. |
| 109400 | In the One-way mode, the 'Side' field can only be set to BOTH. |
| 109500 | symbol not exist |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/leverage'
    method = "POST"
    paramsMap = {
    "leverage": "8",
    "side": "SHORT",
    "symbol": "ETH-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### User's Force Orders

**GET** `/openApi/swap/v2/trade/forceOrders`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| currency | string | No | USDC or USDT |
| autoCloseType | string | No | "LIQUIDATION":liquidation order, "ADL":ADL liquidation order |
| startTime | int64 | No | Start time, unit: millisecond |
| endTime | int64 | No | End time, unit: millisecond |
| limit | int64 | No | The number of returned result sets The default value is 50, the maximum value is 100 |
| timestamp | int64 | Yes | request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| time | int64 | order time, unit: millisecond |
| symbol | string | trading pair, for example: BTC-USDT |
| side | string | buying and selling direction |
| type | string | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order |
| positionSide | string | Position direction, required for single position as BOTH, for both long and short positions only LONG or SHORT can be chosen, defaults to LONG if empty |
| reduceOnly | string | true, false; Default value is false for single position mode; This parameter is not accepted for both long and short positions mode |
| cumQuote | string | transaction amount |
| status | string | order status |
| stopPrice | string | Trigger price |
| price | string | Price |
| origQty | string | original order quantity |
| avgPrice | string | average transaction price |
| executedQty | string | volume |
| orderId | int64 | Order ID |
| profit | string | profit and loss |
| commission | string | Fee |
| updateTime | int64 | StopPrice trigger price types: MARK_PRICE, CONTRACT_PRICE, INDEX_PRICE, default MARK_PRICE |
| workingType | string | update time, unit: millisecond |
| stopGuaranteed | string | true: Enables the guaranteed stop-loss and take-profit feature; false: Disables the feature. The guaranteed stop-loss feature is not enabled by default. Supported order types include: STOP_MARKET: Market stop-loss order / TAKE_PROFIT_MARKET: Market take-profit order / STOP: Limit stop-loss order / TAKE_PROFIT: Limit take-profit order / TRIGGER_LIMIT: Stop-limit order with trigger / TRIGGER_MARKET: Market order with trigger for stop-loss. |

**Request Example**

```json
{
  "symbol": "ATOM-USDT",
  "startTime": "1696291200"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "orders": [
      {
        "symbol": "ATOM-USDT",
        "orderId": 172264854643022330000,
        "side": "SELL",
        "positionSide": "LONG",
        "type": "LIMIT",
        "origQty": "2.36",
        "price": "8.096",
        "executedQty": "2.36",
        "avgPrice": "8.095",
        "cumQuote": "19",
        "stopPrice": "",
        "profit": "-0.9346",
        "commission": "-0.009553",
        "status": "FILLED",
        "time": 1699546393000,
        "updateTime": 1699546393000,
        "clientOrderId": "",
        "leverage": "21X",
        "takeProfit": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": ""
        },
        "stopLoss": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": ""
        },
        "advanceAttr": 0,
        "positionID": 0,
        "takeProfitEntrustPrice": 0,
        "stopLossEntrustPrice": 0,
        "orderType": "",
        "workingType": "MARK_PRICE"
      }
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/forceOrders'
    method = "GET"
    paramsMap = {
    "symbol": "ATOM-USDT",
    "startTime": "1696291200"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Order history

**GET** `/openApi/swap/v2/trade/allOrders`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT.If no symbol is specified, it will query the historical orders for all trading pairs. |
| currency | string | No | USDC or USDT |
| orderId | int64 | No | Only return subsequent orders, and return the latest order by default |
| startTime | int64 | No | Start time, unit: millisecond |
| endTime | int64 | No | End time, unit: millisecond |
| limit | int64 | Yes | number of result sets to return Default: 500 Maximum: 1000 |
| timestamp | int64 | Yes | request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| time | int64 | order time, unit: millisecond |
| symbol | string | trading pair, for example: BTC-USDT.If a specific pair is not provided, a history of transactions for all pairs will be returned |
| side | string | buying and selling direction |
| type | string | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order |
| positionSide | string | Position direction, required for single position as BOTH, for both long and short positions only LONG or SHORT can be chosen, defaults to LONG if empty |
| reduceOnly | string | true, false; Default value is false for single position mode; This parameter is not accepted for both long and short positions mode |
| cumQuote | string | transaction amount |
| status | string | order status |
| stopPrice | string | Trigger price |
| price | string | Price |
| origQty | string | original order quantity |
| avgPrice | string | average transaction price |
| executedQty | string | volume |
| orderId | int64 | Order ID |
| profit | string | profit and loss |
| commission | string | Fee |
| updateTime | int64 | StopPrice trigger price types: MARK_PRICE, CONTRACT_PRICE, INDEX_PRICE, default MARK_PRICE |
| workingType | string | update time, unit: millisecond |
| stopGuaranteed | string | true: Enables the guaranteed stop-loss and take-profit feature; false: Disables the feature. The guaranteed stop-loss feature is not enabled by default. Supported order types include: STOP_MARKET: Market stop-loss order / TAKE_PROFIT_MARKET: Market take-profit order / STOP: Limit stop-loss order / TAKE_PROFIT: Limit take-profit order / TRIGGER_LIMIT: Stop-limit order with trigger / TRIGGER_MARKET: Market order with trigger for stop-loss. |
| triggerOrderId | int64 | trigger order ID associated with this order |
| isTwap | bool | Whether it is a TWAP order, true: yes, false: no |
| mainOrderId | string | TWAP order number |

**Request Example**

```json
{
  "endTime": "1702731995000",
  "limit": "500",
  "startTime": "1702688795000",
  "symbol": "PYTH-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "orders": [
      {
        "symbol": "PYTH-USDT",
        "orderId": 1736007506620112100,
        "side": "SELL",
        "positionSide": "SHORT",
        "type": "LIMIT",
        "origQty": "33",
        "price": "0.3916",
        "executedQty": "33",
        "avgPrice": "0.3916",
        "cumQuote": "13",
        "stopPrice": "",
        "profit": "0.0000",
        "commission": "-0.002585",
        "status": "FILLED",
        "time": 1702731418000,
        "updateTime": 1702731470000,
        "clientOrderId": "",
        "leverage": "15X",
        "takeProfit": {
          "type": "TAKE_PROFIT",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": ""
        },
        "stopLoss": {
          "type": "STOP",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": ""
        },
        "advanceAttr": 0,
        "positionID": 0,
        "takeProfitEntrustPrice": 0,
        "stopLossEntrustPrice": 0,
        "orderType": "",
        "workingType": "MARK_PRICE",
        "stopGuaranteed": false,
        "triggerOrderId": 1736012449498123500
      }
    ]
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 80014 | the query range is more than seven days |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/allOrders'
    method = "GET"
    paramsMap = {
    "endTime": "1702731995000",
    "limit": "500",
    "startTime": "1702688795000",
    "symbol": "PYTH-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Modify Isolated Position Margin

**POST** `/openApi/swap/v2/trade/positionMargin`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| amount | float64 | Yes | margin funds |
| type | string | Yes | adjustment direction 1: increase isolated margin, 2: decrease isolated margin |
| positionSide | string | No | Position direction, and only LONG or SHORT can be selected |
| positionId | int64 | No | Position ID, if it is filled, the system will use the positionId first |
| timestamp | int64 | Yes | request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int64 | error code, 0 means successfully response, others means response failure |
| msg | string | Error Details Description |
| amount | float64 | margin funds |
| type | int64 | adjustment direction 1: increase isolated margin, 2: decrease isolated margin |
| positionId | int64 | Position ID |

**Request Example**

```json
{
  "recvWindow": "10000",
  "symbol": "BTC-USDT",
  "type": "1",
  "amount": "3",
  "positionSide": "LONG"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "amount": 3,
  "type": 1
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/positionMargin'
    method = "POST"
    paramsMap = {
    "recvWindow": "10000",
    "symbol": "BTC-USDT",
    "type": "1",
    "amount": "3",
    "positionSide": "LONG"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query historical transaction orders

**GET** `/openApi/swap/v1/market/historicalTrades`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| fromId | int64 | No | From which transaction ID to start returning. By default, it returns the most recent transaction records |
| symbol | string | No | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| limit | int64 | No | The number of returned result sets The default value is 50, the maximum value is 100 |
| timestamp | int64 | Yes | request timestamp, unit: millisecond |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| time | int64 | transaction time |
| isBuyerMaker | bool | Whether the buyer is the maker of the order (true / false) |
| price | string | transaction price |
| qty | string | transaction quantity |
| quoteQty | string | turnover |
| id | string | transaction ID |

**Request Example**

```json
{
  "fromId": "412551",
  "limit": "500",
  "symbol": "ETH-USDT",
  "recvWindow": "60000"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": [
    {
      "time": 1705063108365,
      "isBuyerMaker": true,
      "price": "2662.83",
      "qty": "0.10",
      "quoteQty": "266.28",
      "id": "8179911"
    },
    {
      "time": 1705063108486,
      "isBuyerMaker": true,
      "price": "2662.82",
      "qty": "0.10",
      "quoteQty": "266.28",
      "id": "8179912"
    }
  ]
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109400 | timestamp is invalid |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/market/historicalTrades'
    method = "GET"
    paramsMap = {
    "fromId": "412551",
    "limit": "500",
    "symbol": "ETH-USDT",
    "recvWindow": "60000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Set Position Mode

**POST** `/openApi/swap/v1/positionSide/dual`

- **Rate Limit**: UID Rate Limit 4/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| dualSidePosition | true | Yes | "true": dual position mode; "false": single position mode |
| timestamp | int64 | Yes | Timestamp of the request in milliseconds |
| recvWindow | int64 | No | The window time for the request to be valid, in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| dualSidePosition | string | "true": dual position mode; "false": single position mode |

**Request Example**

```json
{
  "dualSidePosition": "true"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "dualSidePosition": "true"
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 80001 | margin not enough |
| 80017 | position not exist |
| 80001 | position is not isolated |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/positionSide/dual'
    method = "POST"
    paramsMap = {
    "dualSidePosition": "true"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query position mode

**GET** `/openApi/swap/v1/positionSide/dual`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| timestamp | int64 | Yes | Timestamp of the request in milliseconds |
| recvWindow | int64 | No | The window time for the request to be valid, in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| dualSidePosition | string | "true": dual position mode; "false": single position mode |

**Request Example**

```json
{}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "dualSidePosition": "true"
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109401 | user has pending orders or position |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/positionSide/dual'
    method = "GET"
    paramsMap = {}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Cancel an Existing Order and Send a New Orde

**POST** `/openApi/swap/v1/trade/cancelReplace`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| cancelReplaceMode | string | Yes | STOP_ON_FAILURE: If the order cancellation fails, the replacement order will not continue. ALLOW_FAILURE: Regardless of the success of the order cancellation, the replacement order will proceed. |
| cancelClientOrderId | string | No | The original client-defined order ID to be canceled. The system will convert this field to lowercase. Either cancelClientOrderId or cancelOrderId must be provided. If both parameters are provided, cancelOrderId takes precedence. |
| cancelOrderId | int64 | No | The platform order ID to be canceled. Either cancelClientOrderId or cancelOrderId must be provided. If both parameters are provided, cancelOrderId takes precedence. |
| cancelRestrictions | string | No | ONLY_NEW: If the order status is NEW, the cancellation will succeed. ONLY_PENDING: If the order status is PENDING, the cancellation will succeed. ONLY_PARTIALLY_FILLED: If the order status is PARTIALLY_FILLED, the cancellation will succeed. |
| symbol | string | Yes | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| type | string | Yes | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order / TRAILING_TP_SL: Trailing TakeProfit or StopLoss |
| side | string | Yes | buying and selling direction SELL, BUY |
| positionSide | string | Yes | Position direction, required for single position as BOTH, for both long and short positions only LONG or SHORT can be chosen, defaults to LONG if empty |
| reduceOnly | string | No | true, false; Default value is false for single position mode; This parameter is not accepted for both long and short positions mode |
| price | float64 | No | Price, represents the trailing stop distance in TRAILING_STOP_MARKET and TRAILING_TP_SL |
| quantity | float64 | No | Original quantity, only support units by COIN ,Ordering with quantity U is not currently supported. |
| stopPrice | float64 | No | Trigger price, only required for STOP_MARKET, TAKE_PROFIT_MARKET, STOP, TAKE_PROFIT, TRIGGER_LIMIT, TRIGGER_MARKET |
| priceRate | float64 | No | For type: TRAILING_STOP_MARKET or TRAILING_TP_SL ; Maximum: 1 |
| workingType | string | No | StopPrice trigger price types: MARK_PRICE, CONTRACT_PRICE, INDEX_PRICE, default MARK_PRICE. When the type is STOP or STOP_MARKET, and stopGuaranteed is true, the workingType must only be CONTRACT_PRICE. |
| stopLoss | string | No | Support setting stop loss while placing an order. Only supports type: STOP_MARKET/STOP |
| takeProfit | string | No | Support setting take profit while placing an order. Only supports type: TAKE_PROFIT_MARKET/TAKE_PROFIT |
| clientOrderId | string | No | Customized order ID for users, with a limit of characters from 1 to 40. The system will convert this field to lowercase. Different orders cannot use the same clientOrderId, clientOrderId only supports LIMIT/MARKET order type |
| timestamp | int64 | Yes | request timestamp, unit: millisecond |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |
| closePosition | string | No | true, false; all position squaring after triggering, only support STOP_MARKET and TAKE_PROFIT_MARKET; not used with quantity; comes with only position squaring effect, not used with reduceOnly |
| activationPrice | float64 | No | Used with TRAILING_STOP_MARKET or TRAILING_TP_SL orders, default as the latest price(supporting different workingType) |
| stopGuaranteed | string | No | true: Enables the guaranteed stop-loss and take-profit feature; false: Disables the feature. The guaranteed stop-loss feature is not enabled by default. Supported order types include: STOP_MARKET: Market stop-loss order / TAKE_PROFIT_MARKET: Market take-profit order / STOP: Limit stop-loss order / TAKE_PROFIT: Limit take-profit order / TRIGGER_LIMIT: Stop-limit order with trigger / TRIGGER_MARKET: Market order with trigger for stop-loss. |
| timeInForce | string | No | Time in Force, currently supports PostOnly, GTC, IOC, and FOK |
| positionId | int64 | No | In the Separate Isolated mode, closing a position must be transmitted |

**Response Body**

| filed | data type | description |
|---|---|---|
| cancelResult | string | Cancellation result. true: Cancellation successful, false: Cancellation failed |
| cancelMsg | string | Reason for the cancellation failure |
| cancelResponse | CancelResponse | Information about the canceled order |
| replaceResult | string | Replacement result. true: Replacement successful, false: Replacement failed |
| replaceMsg | string | Reason for the replacement failure |
| newOrderResponse | NewOrderResponse | Information about the new order |

**Request Example**

```json
{
  "cancelReplaceMode": "STOP_ON_FAILURE",
  "cancelClientOrderId": "abc123test",
  "cancelOrderId": 123456789,
  "cancelRestrictions": "ONLY_NEW",
  "symbol": "BTC-USDT",
  "side": "BUY",
  "positionSide": "LONG",
  "type": "MARKET",
  "quantity": 5,
  "takeProfit": "{\"type\": \"TAKE_PROFIT_MARKET\", \"stopPrice\": 31968.0,\"price\": 31968.0,\"workingType\":\"MARK_PRICE\"}"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "cancelResult": "true",
    "cancelMsg": "",
    "cancelResponse": {
      "cancelClientOrderId": "",
      "cancelOrderId": 123456789,
      "symbol": "BTC-USDT",
      "orderId": 123456789,
      "side": "BUY",
      "positionSide": "LONG",
      "type": "LIMIT",
      "origQty": "1.0000",
      "price": "38000.0",
      "executedQty": "0.0000",
      "avgPrice": "0.0",
      "cumQuote": "0",
      "stopPrice": "",
      "profit": "0.0000",
      "commission": "0.000000",
      "status": "PENDING",
      "time": 1706858471000,
      "updateTime": 1706858471000,
      "clientOrderId": "",
      "leverage": "15X",
      "workingType": "MARK_PRICE",
      "onlyOnePosition": false,
      "reduceOnly": false
    },
    "replaceResult": "true",
    "replaceMsg": "",
    "newOrderResponse": {
      "orderId": 987654321,
      "symbol": "BTC-USDT",
      "positionSide": "LONG",
      "side": "BUY",
      "type": "LIMIT",
      "price": 38000,
      "quantity": 1,
      "stopPrice": 0,
      "workingType": "MARK_PRICE",
      "clientOrderId": "",
      "timeInForce": "GTC",
      "priceRate": 0,
      "stopLoss": "{\"type\": \"STOP\", \"stopPrice\": 37000, \"price\": 37000}",
      "takeProfit": "{\"type\": \"TAKE_PROFIT\", \"stopPrice\": 45000, \"price\": 45000}",
      "reduceOnly": false
    }
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/trade/cancelReplace'
    method = "POST"
    paramsMap = {
    "cancelReplaceMode": "STOP_ON_FAILURE",
    "cancelClientOrderId": "abc123test",
    "cancelOrderId": 123456789,
    "cancelRestrictions": "ONLY_NEW",
    "symbol": "BTC-USDT",
    "side": "BUY",
    "positionSide": "LONG",
    "type": "MARKET",
    "quantity": 5,
    "takeProfit": "{\"type\": \"TAKE_PROFIT_MARKET\", \"stopPrice\": 31968.0,\"price\": 31968.0,\"workingType\":\"MARK_PRICE\"}"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Cancel orders in batches and place orders in batches

**POST** `/openApi/swap/v1/trade/batchCancelReplace`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| batchOrders | string | Yes | A batch of orders, string form of LIST<OrderRequest> |
| timestamp | int64 | Yes | request timestamp, unit: millisecond |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int64 | error code, 0 means successfully response, others means response failure |
| msg | string | Error Details Description |
| orderResponse | OrderResponse |  |

**Request Example**

```json
{
  "batchOrders": "[{\"cancelOrderId\": 1753337028434464768, \"cancelReplaceMode\": \"ALLOW_FAILURE\", \"symbol\": \"BTC-USDT\", \"type\": \"LIMIT\", \"side\": \"BUY\", \"positionSide\": \"LONG\", \"price\": 38000, \"quantity\": 1, \"takeProfit\": \"{\\\"type\\\": \\\"TAKE_PROFIT\\\", \\\"quantity\\\": 1, \\\"stopPrice\\\": 45000, \\\"price\\\": 45000}\", \"stopLoss\": \"{\\\"type\\\": \\\"STOP\\\", \\\"quantity\\\": 1, \\\"stopPrice\\\": 37000, \\\"price\\\": 37000}\"}, {\"cancelOrderId\": 1753337028434464768, \"cancelReplaceMode\": \"ALLOW_FAILURE\", \"symbol\": \"BTC-USDT\", \"type\": \"LIMIT\", \"side\": \"BUY\", \"positionSide\": \"LONG\", \"price\": 38000, \"quantity\": 1, \"takeProfit\": \"{\\\"type\\\": \\\"TAKE_PROFIT\\\", \\\"quantity\\\": 1, \\\"stopPrice\\\": 45000, \\\"price\\\": 45000}\", \"stopLoss\": \"{\\\"type\\\": \\\"STOP\\\", \\\"quantity\\\": 1, \\\"stopPrice\\\": 37000, \\\"price\\\": 37000}\"}, {\"cancelOrderId\": 1753337028434464768, \"cancelReplaceMode\": \"ALLOW_FAILURE\", \"symbol\": \"BTC-USDT\", \"type\": \"LIMIT\", \"side\": \"BUY\", \"positionSide\": \"LONG\", \"price\": 38000, \"quantity\": 1, \"takeProfit\": \"{\\\"type\\\": \\\"TAKE_PROFIT\\\", \\\"quantity\\\": 1, \\\"stopPrice\\\": 45000, \\\"price\\\": 45000}\", \"stopLoss\": \"{\\\"type\\\": \\\"STOP\\\", \\\"quantity\\\": 1, \\\"stopPrice\\\": 37000, \\\"price\\\": 37000}\"}]"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": [
    {
      "cancelResult": "true",
      "cancelMsg": "",
      "cancelResponse": {
        "cancelClientOrderId": "",
        "cancelOrderId": 1753337028434464800,
        "symbol": "BTC-USDT",
        "orderId": 1753337028434464800,
        "side": "BUY",
        "positionSide": "LONG",
        "type": "LIMIT",
        "origQty": "10.0000",
        "price": "38000.0",
        "executedQty": "0.0000",
        "avgPrice": "0.0",
        "cumQuote": "0",
        "stopPrice": "",
        "profit": "0.0000",
        "commission": "0.000000",
        "status": "PENDING",
        "time": 1706863098000,
        "updateTime": 1706863097000,
        "clientOrderId": "",
        "leverage": "15X",
        "workingType": "MARK_PRICE",
        "onlyOnePosition": false,
        "reduceOnly": false
      },
      "replaceResult": "true",
      "ReplaceMsg": "",
      "newOrderResponse": {
        "orderId": 1753337098747777000,
        "symbol": "BTC-USDT",
        "positionSide": "LONG",
        "side": "BUY",
        "type": "LIMIT",
        "price": 38000,
        "quantity": 1,
        "stopPrice": 0,
        "workingType": "MARK_PRICE",
        "clientOrderId": "",
        "timeInForce": "GTC",
        "priceRate": 0,
        "stopLoss": "{\"type\": \"STOP\", \"quantity\": 1, \"stopPrice\": 37000, \"price\": 37000}",
        "takeProfit": "{\"type\": \"TAKE_PROFIT\", \"quantity\": 1, \"stopPrice\": 45000, \"price\": 45000}",
        "reduceOnly": false
      }
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/trade/batchCancelReplace'
    method = "POST"
    paramsMap = {
    "batchOrders": "[{\"cancelOrderId\": 1753337028434464768, \"cancelReplaceMode\": \"ALLOW_FAILURE\", \"symbol\": \"BTC-USDT\", \"type\": \"LIMIT\", \"side\": \"BUY\", \"positionSide\": \"LONG\", \"price\": 38000, \"quantity\": 1, \"takeProfit\": \"{\\\"type\\\": \\\"TAKE_PROFIT\\\", \\\"quantity\\\": 1, \\\"stopPrice\\\": 45000, \\\"price\\\": 45000}\", \"stopLoss\": \"{\\\"type\\\": \\\"STOP\\\", \\\"quantity\\\": 1, \\\"stopPrice\\\": 37000, \\\"price\\\": 37000}\"}, {\"cancelOrderId\": 1753337028434464768, \"cancelReplaceMode\": \"ALLOW_FAILURE\", \"symbol\": \"BTC-USDT\", \"type\": \"LIMIT\", \"side\": \"BUY\", \"positionSide\": \"LONG\", \"price\": 38000, \"quantity\": 1, \"takeProfit\": \"{\\\"type\\\": \\\"TAKE_PROFIT\\\", \\\"quantity\\\": 1, \\\"stopPrice\\\": 45000, \\\"price\\\": 45000}\", \"stopLoss\": \"{\\\"type\\\": \\\"STOP\\\", \\\"quantity\\\": 1, \\\"stopPrice\\\": 37000, \\\"price\\\": 37000}\"}, {\"cancelOrderId\": 1753337028434464768, \"cancelReplaceMode\": \"ALLOW_FAILURE\", \"symbol\": \"BTC-USDT\", \"type\": \"LIMIT\", \"side\": \"BUY\", \"positionSide\": \"LONG\", \"price\": 38000, \"quantity\": 1, \"takeProfit\": \"{\\\"type\\\": \\\"TAKE_PROFIT\\\", \\\"quantity\\\": 1, \\\"stopPrice\\\": 45000, \\\"price\\\": 45000}\", \"stopLoss\": \"{\\\"type\\\": \\\"STOP\\\", \\\"quantity\\\": 1, \\\"stopPrice\\\": 37000, \\\"price\\\": 37000}\"}]"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Cancel All After

**POST** `/openApi/swap/v2/trade/cancelAllAfter`

- **Rate Limit**: UID Rate Limit 1/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| type | string | Yes | Request type: ACTIVATE-Activate, CLOSE-Close |
| timeOut | int64 | Yes | Activate countdown time (seconds), range: 10s-120s |

**Response Body**

| filed | data type | description |
|---|---|---|
| triggerTime | int64 | Trigger time for deleting all pending orders |
| status | 狀態 | ACTIVATED (Activation successful)/CLOSED (Closed successfully)/FAILED (Failed) |
| note | string | Explanation |

**Request Example**

```json
{
  "type": "ACTIVATE",
  "timeOut": 10
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "debugMsg": "",
  "data": {
    "triggerTime": 1710389137,
    "status": "ACTIVATED",
    "note": "All your spot pending orders will be closed automatically at 2024-03-14 04:05:37 UTC(+0),before that you can cancel the timer, or extend triggerTime time by this request"
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/cancelAllAfter'
    method = "POST"
    paramsMap = {
    "type": "ACTIVATE",
    "timeOut": 10
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Close position by position ID

**POST** `/openApi/swap/v1/trade/closePosition`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| positionId | string | Yes | Position ID, will close the position with market price |
| timestamp | int64 | Yes | Request timestamp, in milliseconds |
| recvWindow | int64 | No | Request valid time window value, in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int64 | Error code, 0 indicates success, non-zero indicates abnormal failure |
| msg | string | Error message prompt |
| data | Data |  |

**Request Example**

```json
{
  "positionId": "1769649551460794368"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "timestamp": 0,
  "data": {
    "orderId": 1769649628749234200,
    "positionId": "1769649551460794368",
    "symbol": "BTC-USDT",
    "side": "Ask",
    "type": "Market",
    "positionSide": "BOTH",
    "origQty": "1.0000"
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/trade/closePosition'
    method = "POST"
    paramsMap = {
    "positionId": "1769649551460794368"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### All Orders

**GET** `/openApi/swap/v1/trade/fullOrder`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT.If no symbol is specified, it will query the orders for all trading pairs. |
| orderId | int64 | No | Only return subsequent orders, and return the latest order by default |
| startTime | int64 | No | Start time, unit: millisecond |
| endTime | int64 | No | End time, unit: millisecond |
| limit | int64 | Yes | number of result sets to return Default: 500 Maximum: 1000 |
| timestamp | int64 | Yes | request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| time | int64 | order time, unit: millisecond |
| symbol | string | trading pair, for example: BTC-USDT |
| side | string | buying and selling direction |
| type | string | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order |
| positionSide | string | Position direction, required for single position as BOTH, for both long and short positions only LONG or SHORT can be chosen, defaults to LONG if empty |
| reduceOnly | string | true, false; Default value is false for single position mode; This parameter is not accepted for both long and short positions mode |
| cumQuote | string | transaction amount |
| status | string | order status |
| stopPrice | string | Trigger price |
| price | string | Price |
| origQty | string | original order quantity |
| avgPrice | string | average transaction price |
| executedQty | string | volume |
| orderId | int64 | Order ID |
| profit | string | profit and loss |
| commission | string | Fee |
| updateTime | int64 | StopPrice trigger price types: MARK_PRICE, CONTRACT_PRICE, INDEX_PRICE, default MARK_PRICE |
| workingType | string | update time, unit: millisecond |
| stopGuaranteed | string | true: Enables the guaranteed stop-loss and take-profit feature; false: Disables the feature. The guaranteed stop-loss feature is not enabled by default. Supported order types include: STOP_MARKET: Market stop-loss order / TAKE_PROFIT_MARKET: Market take-profit order / STOP: Limit stop-loss order / TAKE_PROFIT: Limit take-profit order / TRIGGER_LIMIT: Stop-limit order with trigger / TRIGGER_MARKET: Market order with trigger for stop-loss. |
| triggerOrderId | int64 | trigger order ID associated with this order |
| isTwap | bool | Whether it is a TWAP order, true: yes, false: no |
| mainOrderId | string | TWAP order number |

**Request Example**

```json
{
  "endTime": "1702731995000",
  "limit": "500",
  "startTime": "1702688795000",
  "symbol": "PYTH-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "orders": [
      {
        "symbol": "PYTH-USDT",
        "orderId": 1736007506620112100,
        "side": "SELL",
        "positionSide": "SHORT",
        "type": "LIMIT",
        "origQty": "33",
        "price": "0.3916",
        "executedQty": "33",
        "avgPrice": "0.3916",
        "cumQuote": "13",
        "stopPrice": "",
        "profit": "0.0000",
        "commission": "-0.002585",
        "status": "FILLED",
        "time": 1702731418000,
        "updateTime": 1702731470000,
        "clientOrderId": "",
        "leverage": "15X",
        "takeProfit": {
          "type": "TAKE_PROFIT",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": ""
        },
        "stopLoss": {
          "type": "STOP",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": ""
        },
        "advanceAttr": 0,
        "positionID": 0,
        "takeProfitEntrustPrice": 0,
        "stopLossEntrustPrice": 0,
        "orderType": "",
        "workingType": "MARK_PRICE",
        "stopGuaranteed": false,
        "triggerOrderId": 1736012449498123500,
        "isTwap": true,
        "mainOrderId": "21312431241234"
      }
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/trade/fullOrder'
    method = "GET"
    paramsMap = {
    "endTime": "1702731995000",
    "limit": "500",
    "startTime": "1702688795000",
    "symbol": "PYTH-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Position and Maintenance Margin Ratio

**GET** `/openApi/swap/v1/maintMarginRatio`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | Trading pair, e.g., BTC-USDT, please use uppercase letters |
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| tier | string | Layer |
| symbol | string | Trading pair |
| minPositionVal | string | Minimum position value |
| maxPositionVal | string | Maximum position value |
| maintMarginRatio | string | Maintenance margin ratio |
| maintAmount | string | Maintenance margin quick calculation amount |

**Request Example**

```json
{
  "symbol": "BTC-USDT",
  "recvWindow": "5000"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "timestamp": 1716388317402,
  "data": [
    {
      "tier": "Tier 1",
      "symbol": "BTC-USDT",
      "minPositionVal": "0",
      "maxPositionVal": "150000",
      "maintMarginRatio": "0.003800",
      "maintAmount": "0.000000"
    },
    {
      "tier": "Tier 2",
      "symbol": "BTC-USDT",
      "minPositionVal": "150000",
      "maxPositionVal": "900000",
      "maintMarginRatio": "0.004000",
      "maintAmount": "30.000000"
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/maintMarginRatio'
    method = "GET"
    paramsMap = {
    "symbol": "BTC-USDT",
    "recvWindow": "5000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query historical transaction details

**GET** `/openApi/swap/v2/trade/fillHistory`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | Trading pair, e.g., BTC-USDT, please use uppercase letters |
| currency | string | No | USDC or USDT |
| orderId | int64 | No | If orderId is provided, only the filled orders of that orderId are returned |
| lastFillId | int64 | No | The last tradeId of the last query, default is 0 if not filled in. |
| pageIndex | int64 | No | Starting timestamp in milliseconds |
| pageSize | int64 | No | End timestamp in milliseconds |
| startTs | int64 | Yes | request timestamp, unit: millisecond |
| endTs | int64 | Yes | Request valid time window value, Unit: milliseconds |
| timestamp | int64 | Yes | The page number must be greater than 0, if not filled in, the default is 1 |
| recvWindow | int64 | No | The size of each page must be greater than 0, the maximum value is 1000, if you do not fill in, then the default 50 |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | trading pair, for example: BTC-USDT |
| qty | string | Transaction quantity |
| quoteQty | string | Transaction price |
| price | string | Transaction amount |
| commission | string | commission |
| commissionAsset | string | Asset unit, usually USDT |
| tradeId | string | order id |
| orderId | string | trade id |
| filledTime | string | Match the transaction time in the format of 2006-01-02T15:04:05.999+0800 |
| side | string | buying and selling direction |
| positionSide | string | Position direction, required for single position as BOTH, for both long and short positions only LONG or SHORT can be chosen, defaults to LONG if empty |
| role | string | Active selling and buying, taker: active buying, maker: active selling |
| total | int64 | total records |

**Request Example**

```json
{
  "endTs": "1702731530000",
  "startTs": "1702724330000",
  "symbol": "WLD-USDT",
  "lastFillId": 130753,
  "pageSize": 50
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "fill_history_orders": [
      {
        "filledTm": "2023-12-16T20:58:36Z",
        "volume": "4.10",
        "price": "3.1088",
        "qty": "12.74",
        "quoteQty": "211.40",
        "commission": "-0.0025",
        "commissionAsset": "USDT",
        "orderId": "1736007768311123456",
        "tradeId": "241512",
        "filledTime": "2023-12-16T20:58:36.000+0800",
        "symbol": "WLD-USDT",
        "role": "maker",
        "side": "buy",
        "positionSide": "short"
      }
    ],
    "total": 290
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/fillHistory'
    method = "GET"
    paramsMap = {
    "endTs": "1702731530000",
    "startTs": "1702724330000",
    "symbol": "WLD-USDT",
    "lastFillId": 130753,
    "pageSize": 50
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Position History

**GET** `/openApi/swap/v1/trade/positionHistory`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | Trading pair, e.g.: BTC-USDT, please use uppercase letters |
| currency | string | No | USDC or USDT |
| timestamp | int64 | Yes | Request timestamp, in milliseconds |
| positionId | int64 | No | Position ID, if not provided, all position histories of the relevant trading pair will be returned by default |
| startTs | int64 | Yes | Start timestamp, in milliseconds, maximum time span is three months, if not provided, the default start time is 90 days ago |
| endTs | int64 | Yes | End timestamp, in milliseconds, maximum time span is three months, if not provided, the default end time is the current time |
| pageIndex | int64 | No | Page number, must be greater than 0, if not provided, the default is 1 |
| pageSize | int64 | No | Page size, must be greater than 0, maximum value is 100, if not provided, the default is 1000 |
| recvWindow | int64 | No | Request valid window value, in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | Trading pair, e.g.: BTC-USDT |
| positionId | string | Position ID |
| positionSide | string | Position side LONG/SHORT |
| isolated | bool | Isolated mode, true: isolated mode, false: cross margin |
| closeAllPositions | bool | All positions closed |
| positionAmt | string | Position amount |
| closePositionAmt | string | Closed position amount |
| realisedProfit | string | Realized profit and loss |
| netProfit | string | Net profit and loss |
| avgClosePrice | float64 | Average close price |
| avgPrice | string | Average open price |
| leverage | int64 | Leverage |
| positionCommission | string | Commission fee |
| totalFunding | string | Funding fee |
| openTime | int64 | Open time |
| openTime | int64 | Close time |

**Request Example**

```json
{
  "recvWindow": "0",
  "symbol": "BNB-USDT",
  "pageId": 0,
  "pageSize": 20,
  "startTime": 1700409600000,
  "endTime": 1703001599000
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": [
    {
      "positionId": "180870089***590996",
      "symbol": "BTC-USDT",
      "isolated": false,
      "positionSide": "LONG",
      "openTime": 1720062873000,
      "updateTime": 1720062878000,
      "avgPrice": "58942.31",
      "avgClosePrice": "58930.00",
      "realisedProfit": "-0.04",
      "netProfit": "-0.16",
      "positionAmt": "33.0000",
      "closePositionAmt": "33.0000",
      "leverage": 20,
      "closeAllPositions": true,
      "positionCommission": "-0.11669358690000001",
      "totalFunding": "0.00000000000000001388"
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/trade/positionHistory'
    method = "GET"
    paramsMap = {
    "recvWindow": "0",
    "symbol": "BNB-USDT",
    "pageId": 0,
    "pageSize": 20,
    "startTime": 1700409600000,
    "endTime": 1703001599000
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Isolated Margin Change History

**GET** `/openApi/swap/v1/positionMargin/history`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | Trading pair, e.g.: BTC-USDT, please use uppercase letters |
| positionId | string | Yes | Position ID |
| startTime | int64 | Yes | Start timestamp, in milliseconds |
| endTime | int64 | Yes | End timestamp, in milliseconds |
| pageIndex | int64 | Yes | Page number, must be greater than 0, if not provided, the default is 1 |
| pageSize | int64 | Yes | Page size, must be greater than 0, maximum value is 100 |
| timestamp | int64 | Yes | Request timestamp, in milliseconds |
| recvWindow | int64 | No | Request valid window value, in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | Trading pair, e.g.: BTC-USDT |
| positionId | string | Position ID |
| changeReason | string | ManualMarginAddition: Manually add margin / ManualMarginReduction: Reduce margin manually / IncreaseLeverage: Increase leverage / ReduceLeverage: Reduce leverage / OpenPosition: Open position / ClosePosition: Close position / Liquidation: Liquidation / ADL:Automatically reduce positions / CloseOpenPosition : Close first and then open a position /FundingFeeSettlement: Funding rate settlement/ AutoMarginAddition: Automatic margin addition |
| marginChange | string | change amount |
| marginAfterChange | string | Total amount after change |
| time | int64 | Change time |

**Request Example**

```json
{
  "symbol": "BNB-USDT",
  "positionId": "1847596444958068736",
  "startTime": 1728722649000,
  "endTime": 1729336359406,
  "pageIndex": 1,
  "pageSize": 2,
  "timestamp": 1702731661854,
  "recvWindow": "0"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "timestamp": 1702731661854,
  "data": {
    "records": [
      {
        "symbol": "BTC-USDT",
        "positionId": "1847596444958068736",
        "changeReason": "OpenPosition",
        "marginChange": "7586.46841066",
        "marginAfterChange": "7586.46841066",
        "time": 1729336294000
      }
    ],
    "total": 4
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/positionMargin/history'
    method = "GET"
    paramsMap = {
    "symbol": "BNB-USDT",
    "positionId": "1847596444958068736",
    "startTime": 1728722649000,
    "endTime": 1729336359406,
    "pageIndex": 1,
    "pageSize": 2,
    "timestamp": 1702731661854,
    "recvWindow": "0"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Apply VST

**POST** `/openApi/swap/v2/trade/getVst`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value in milliseconds |
| adjustType | string | No | Adjustment type: 0 means increase, 1 means decrease |
| amount | int64 | No | Adjustment amount |

**Response Body**

| filed | data type | description |
|---|---|---|
| adjustType | string | Adjustment type: 0 means increase, 1 means decrease |
| amount | string | Amount of VST applied in this request |

**Request Example**

```json
{
  "adjustType": "0",
  "amount": 500000
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "timestamp": 1730863321895,
  "data": {
    "adjustType": "0",
    "amount": "500000"
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109500 | Account Service Unavailable, err:symbol not exist |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/getVst'
    method = "POST"
    paramsMap = {
    "adjustType": "0",
    "amount": 500000
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Place TWAP Order

**POST** `/openApi/swap/v1/twap/order`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | Trading pair, for example: BTC-USDT, please use capital letters |
| side | string | Yes | Buying and selling direction SELL, BUY |
| positionSide | string | Yes | LONG or SHORT |
| priceType | string | Yes | Price limit type; constant: price interval / percentage: slippage |
| priceVariance | string | Yes | When type is constant, it represents the price difference (unit is USDT), when type is percentage, it represents the slippage ratio (unit is %) |
| triggerPrice | string | Yes | Trigger price, this price is the condition that limits the execution of strategy orders. For buying, when the market price is lower than the limit price, an order will be placed based on the set ratio or price distance of the selling price; for selling, when the market price is higher than the limit price, an order will be placed for the selling price down. Take the set ratio or price gap to place an order. |
| interval | int64 | Yes | After the strategic order is split, the time interval for order placing is between 5-120s. |
| amountPerOrder | string | Yes | The quantity of a single order. After the strategy order is split, the maximum order quantity for a single order。 |
| totalAmount | string | Yes | The total number of orders. The total trading volume of strategy orders, which may be split into multiple order executions. |
| timestamp | int64 | Yes | The timestamp of the request in milliseconds |
| recvWindow | int64 | No | Request valid time window value, unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| mainOrderId | string | twap order number |

**Request Example**

```json
{
  "symbol": "BNB-USDT",
  "positionId": "1847596444958068736",
  "startTime": 1728722649000,
  "endTime": 1729336359406,
  "pageIndex": 1,
  "pageSize": 2,
  "timestamp": 1702731661854,
  "recvWindow": "0"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "timestamp": 1702731661854,
  "data": {
    "records": [
      {
        "symbol": "BTC-USDT",
        "positionId": "1847596444958068736",
        "changeReason": "OpenPosition",
        "marginChange": "7586.46841066",
        "marginAfterChange": "7586.46841066",
        "time": 1729336294000
      }
    ],
    "total": 4
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/twap/order'
    method = "POST"
    paramsMap = {
    "symbol": "BNB-USDT",
    "positionId": "1847596444958068736",
    "startTime": 1728722649000,
    "endTime": 1729336359406,
    "pageIndex": 1,
    "pageSize": 2,
    "timestamp": 1702731661854,
    "recvWindow": "0"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query TWAP Entrusted Order

**GET** `/openApi/swap/v1/twap/openOrders`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | Trading pair, for example: BTC-USDT, please use capital letters |
| timestamp | int64 | Yes | the timestamp of the request in milliseconds |
| recvWindow | int64 | No | Request valid time window value, unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | Trading pair, for example: BTC-USDT |
| mainOrderId | string | TWAP order number |
| side | string | buying and selling direction; SELL, BUY |
| positionSide | string | LONG or SHORT |
| priceType | string | Price limit type, constant: price interval, percentage: slippage |
| priceVariance | string | When type is constant, it represents the price difference (unit is USDT), when type is percentage, it represents the slippage ratio (unit is %) |
| triggerPrice | string | Trigger price, this price is the condition that limits the execution of strategy orders. For buying, when the market price is lower than the limit price, an order will be placed based on the set ratio or price distance of the selling price; for selling, when the market price is higher than the limit price, an order will be placed for the selling price down. Take the set ratio or price gap to place an order. |
| interval | int64 | After the strategic order is split, the time interval for order placing is between 5-120s |
| amountPerOrder | string | The quantity of a single order. After the strategy order is split, the maximum order quantity for a single order. |
| totalAmount | string | The total number of orders. The total trading volume of strategy orders, which may be split into multiple order executions. |
| orderStatus | string | New: New/Running: In operation/Canceling: Cancellation of order/Filled: Fully filled/PartiallyFilled: Partially filled/Pending: Not triggered/PartiallyFilledAndResidueFailed: Partially filled (remaining order failed), algorithm order status/PartiallyFilledAndResidueCancelled: Partially filled ( Remaining cancellation), algorithm order status/Cancelled: Canceled (no partial deal exists)/Failed: Order failed (no partial deal exists) |
| executedQty | string | Volume |
| duration | int64 | Execution time, in seconds. The order will be canceled after the execution time expires. |
| maxDuration | int64 | Maximum execution time execution time, unit: seconds. |
| createdTime | int64 | Order creation time, unit: milliseconds |
| updateTime | int64 | Order update time, unit: milliseconds |

**Request Example**

```json
{
  "symbol": "BNB-USDT",
  "timestamp": 1702731661854,
  "recvWindow": "0"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "timestamp": 1702731661854,
  "data": {
    "list": [
      {
        "symbol": "BNB-USDT",
        "side": "BUY",
        "positionSide": "LONG",
        "priceType": "constant",
        "priceVariance": "2000",
        "triggerPrice": "68000",
        "interval": 8,
        "amountPerOrder": "0.111",
        "totalAmount": "0.511",
        "orderStatus": "Running",
        "executedQty": "0.1",
        "duration": 800,
        "maxDuration": 9000,
        "createdTime": 1702731661854,
        "updateTime": 1702731661854
      }
    ],
    "total": 1
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/twap/openOrders'
    method = "GET"
    paramsMap = {
    "symbol": "BNB-USDT",
    "timestamp": 1702731661854,
    "recvWindow": "0"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query TWAP Historical Orders

**GET** `/openApi/swap/v1/twap/historyOrders`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | Trading pair, for example: BTC-USDT, please use capital letters |
| pageIndex | int64 | Yes | Paging parameters, the minimum value is 1 |
| pageSize | int64 | Yes | Number of result sets returned; maximum: 1000 |
| startTime | int64 | Yes | Start time, unit: milliseconds |
| endTime | int64 | Yes | End time, unit: milliseconds |
| timestamp | int64 | Yes | The timestamp of the request in milliseconds |
| recvWindow | int64 | No | Request valid time window value, unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | Trading pair, for example: BTC-USDT |
| mainOrderId | string | twap order number |
| side | string | buying and selling direction; SELL, BUY |
| positionSide | string | LONG or SHORT |
| priceType | string | Price limit type, constant: price interval, percentage: slippage |
| priceVariance | string | When type is constant, it represents the price difference (unit is USDT), when type is percentage, it represents the slippage ratio (unit is %) |
| triggerPrice | string | Trigger price, this price is the condition that limits the execution of strategy orders. For buying, when the market price is lower than the limit price, an order will be placed based on the set ratio or price distance of the selling price; for selling, when the market price is higher than the limit price, an order will be placed for the selling price down. Take the set ratio or price gap to place an order. |
| interval | int64 | After the strategic order is split, the time interval for order placing is between 5-120s |
| amountPerOrder | string | The quantity of a single order. After the strategy order is split, the maximum order quantity for a single order. |
| totalAmount | string | The total number of orders. The total trading volume of strategy orders, which may be split into multiple order executions. |
| orderStatus | string | New: New/Running: In operation/Canceling: Cancellation of order/Filled: Fully filled/PartiallyFilled: Partially filled/Pending: Not triggered/PartiallyFilledAndResidueFailed: Partially filled (remaining order failed), algorithm order status/PartiallyFilledAndResidueCancelled: Partially filled ( Remaining cancellation), algorithm order status/Cancelled: Canceled (no partial deal exists)/Failed: Order failed (no partial deal exists) |
| executedQty | string | Volume |
| duration | int64 | Execution time, in seconds. The order will be canceled after the execution time expires. |
| maxDuration | int64 | Maximum execution time execution time, unit: seconds. |
| createdTime | int64 | Order creation time, unit: milliseconds |
| updateTime | int64 | Order update time, unit: milliseconds |

**Request Example**

```json
{
  "symbol": "BNB-USDT",
  "pageIndex": 1,
  "pageSize": 100,
  "startTime": 1702731661854,
  "endTime": 1702738661854,
  "timestamp": 1702731661854,
  "recvWindow": "0"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "timestamp": 1702731661854,
  "data": {
    "list": [
      {
        "symbol": "BNB-USDT",
        "side": "BUY",
        "positionSide": "LONG",
        "priceType": "constant",
        "priceVariance": "2000",
        "triggerPrice": "68000",
        "interval": 8,
        "amountPerOrder": "0.111",
        "totalAmount": "0.511",
        "orderStatus": "Running",
        "executedQty": "0.1",
        "duration": 800,
        "maxDuration": 9000,
        "createdTime": 1702731661854,
        "updateTime": 1702731661854
      }
    ],
    "total": 1
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/twap/historyOrders'
    method = "GET"
    paramsMap = {
    "symbol": "BNB-USDT",
    "pageIndex": 1,
    "pageSize": 100,
    "startTime": 1702731661854,
    "endTime": 1702738661854,
    "timestamp": 1702731661854,
    "recvWindow": "0"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### TWAP Order Details

**GET** `/openApi/swap/v1/twap/orderDetail`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| mainOrderId | string | Yes | TWAP commission order number |
| timestamp | int64 | Yes | The timestamp of the request in milliseconds |
| recvWindow | int64 | No | Request valid time window value, unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | Trading pair, for example: BTC-USDT |
| mainOrderId | string | TWAP order number |
| side | string | buying and selling direction; SELL, BUY |
| positionSide | string | LONG or SHORT |
| priceType | string | Price limit type, constant: price interval, percentage: slippage |
| priceVariance | string | When type is constant, it represents the price difference (unit is USDT), when type is percentage, it represents the slippage ratio (unit is %) |
| triggerPrice | string | Trigger price, this price is the condition that limits the execution of strategy orders. For buying, when the market price is lower than the limit price, an order will be placed based on the set ratio or price distance of the selling price; for selling, when the market price is higher than the limit price, an order will be placed for the selling price down. Take the set ratio or price gap to place an order. |
| interval | int64 | After the strategic order is split, the time interval for order placing is between 5-120s |
| amountPerOrder | string | The quantity of a single order. After the strategy order is split, the maximum order quantity for a single order. |
| totalAmount | string | The total number of orders. The total trading volume of strategy orders, which may be split into multiple order executions. |
| orderStatus | string | New: New/Running: In operation/Canceling: Cancellation of order/Filled: Fully filled/PartiallyFilled: Partially filled/Pending: Not triggered/PartiallyFilledAndResidueFailed: Partially filled (remaining order failed), algorithm order status/PartiallyFilledAndResidueCancelled: Partially filled ( Remaining cancellation), algorithm order status/Cancelled: Canceled (no partial deal exists)/Failed: Order failed (no partial deal exists) |
| executedQty | string | Volume |
| duration | int64 | Execution time, in seconds. The order will be canceled after the execution time expires. |
| maxDuration | int64 | Maximum execution time execution time, unit: seconds. |
| createdTime | int64 | Order creation time, unit: milliseconds |
| updateTime | int64 | Order update time, unit: milliseconds |

**Request Example**

```json
{
  "mainOrderId": "12312435134",
  "timestamp": 1702731661854,
  "recvWindow": "0"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "timestamp": 1702731661854,
  "data": {
    "symbol": "BNB-USDT",
    "side": "BUY",
    "positionSide": "LONG",
    "priceType": "constant",
    "priceVariance": "2000",
    "triggerPrice": "68000",
    "interval": 8,
    "amountPerOrder": "0.111",
    "totalAmount": "0.511",
    "orderStatus": "Running",
    "executedQty": "0.1",
    "duration": 800,
    "maxDuration": 9000,
    "createdTime": 1702731661854,
    "updateTime": 1702731661854
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/twap/orderDetail'
    method = "GET"
    paramsMap = {
    "mainOrderId": "12312435134",
    "timestamp": 1702731661854,
    "recvWindow": "0"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Cancel TWAP Order

**POST** `/openApi/swap/v1/twap/cancelOrder`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| mainOrderId | string | Yes | TWAP order number |
| timestamp | int64 | Yes | The timestamp of the request in milliseconds |
| recvWindow | int64 | No | Request valid time window value, unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | Trading pair, for example: BTC-USDT |
| mainOrderId | string | TWAP order number |
| side | string | buying and selling direction; SELL, BUY |
| positionSide | string | LONG or SHORT |
| priceType | string | Price limit type, constant: price interval, percentage: slippage |
| priceVariance | string | When type is constant, it represents the price difference (unit is USDT), when type is percentage, it represents the slippage ratio (unit is %) |
| triggerPrice | string | Trigger price, this price is the condition that limits the execution of strategy orders. For buying, when the market price is lower than the limit price, an order will be placed based on the set ratio or price distance of the selling price; for selling, when the market price is higher than the limit price, an order will be placed for the selling price down. Take the set ratio or price gap to place an order. |
| interval | int64 | After the strategic order is split, the time interval for order placing is between 5-120s |
| amountPerOrder | string | The quantity of a single order. After the strategy order is split, the maximum order quantity for a single order. |
| totalAmount | string | The total number of orders. The total trading volume of strategy orders, which may be split into multiple order executions. |
| orderStatus | string | New: New/Running: In operation/Canceling: Cancellation of order/Filled: Fully filled/PartiallyFilled: Partially filled/Pending: Not triggered/PartiallyFilledAndResidueFailed: Partially filled (remaining order failed), algorithm order status/PartiallyFilledAndResidueCancelled: Partially filled ( Remaining cancellation), algorithm order status/Cancelled: Canceled (no partial deal exists)/Failed: Order failed (no partial deal exists) |
| executedQty | string | Volume |
| duration | int64 | Execution time, in seconds. The order will be canceled after the execution time expires. |
| maxDuration | int64 | Maximum execution time execution time, unit: seconds. |
| createdTime | int64 | Order creation time, unit: milliseconds |
| updateTime | int64 | Order update time, unit: milliseconds |

**Request Example**

```json
{
  "mainOrderId": "12312435134",
  "timestamp": 1702731661854,
  "recvWindow": "0"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "timestamp": 1702731661854,
  "data": {
    "symbol": "BNB-USDT",
    "side": "BUY",
    "positionSide": "LONG",
    "priceType": "constant",
    "priceVariance": "2000",
    "triggerPrice": "68000",
    "interval": 8,
    "amountPerOrder": "0.111",
    "totalAmount": "0.511",
    "orderStatus": "Running",
    "executedQty": "0.1",
    "duration": 800,
    "maxDuration": 9000,
    "createdTime": 1702731661854,
    "updateTime": 1702731661854
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/twap/cancelOrder'
    method = "POST"
    paramsMap = {
    "mainOrderId": "12312435134",
    "timestamp": 1702731661854,
    "recvWindow": "0"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Switch Multi-Assets Mode

**POST** `/openApi/swap/v1/trade/assetMode`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| assetMode | string | Yes | multi-assets mode, singleAssetMode or multiAssetsMode |
| timestamp | int64 | Yes | request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| assetMode | string | multi-assets mode, singleAssetMode or multiAssetsMode |

**Request Example**

```json
{
  "assetMode": "multiAssetsMode",
  "timestamp": 1730863321895
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "assetMode": "multiAssetsMode"
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109500 | Account Service Unavailable, err:symbol not exist |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/trade/assetMode'
    method = "POST"
    paramsMap = {
    "assetMode": "multiAssetsMode",
    "timestamp": 1730863321895
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Multi-Assets Mode

**GET** `/openApi/swap/v1/trade/assetMode`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| timestamp | int64 | Yes | request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| assetMode | string | multi-assets mode, singleAssetMode or multiAssetsMode |

**Request Example**

```json
{
  "timestamp": 1730863321895
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "assetMode": "multiAssetsMode"
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109500 | Account Service Unavailable, err:symbol not exist |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/trade/assetMode'
    method = "GET"
    paramsMap = {
    "timestamp": 1730863321895
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Multi-Assets Rules

**GET** `/openApi/swap/v1/trade/multiAssetsRules`

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| timestamp | int64 | Yes | request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| marginAssets | string | Margin assets, such as BTC, ETH, etc. |
| ltv | string | Loan-to-Value ratio, value conversion ratio used when calculating available margin. |
| collateralValueRatio | string | Collateral ratio, value conversion ratio used when calculating risk rate. |
| maxTransfer | string | Transfer limit, maximum amount that can be transferred in. Empty means no limit. |
| indexPrice | string | Current latest USD index price for the asset. |

**Request Example**

```json
{
  "timestamp": 1730863321895
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": [
    {
      "marginAssets": "USDT",
      "ltv": "99.99%",
      "collateralValueRatio": "99.99%",
      "maxTransfer": "",
      "indexPrice": "1.0006981800"
    },
    {
      "marginAssets": "USDC",
      "ltv": "99.99%",
      "collateralValueRatio": "99.99%",
      "maxTransfer": "",
      "indexPrice": "0.9998772499"
    },
    {
      "marginAssets": "TRX",
      "ltv": "85.00%",
      "collateralValueRatio": "95.00%",
      "maxTransfer": "300000",
      "indexPrice": "0.1778813333"
    },
    {
      "marginAssets": "DOGE",
      "ltv": "95.00%",
      "collateralValueRatio": "95.00%",
      "maxTransfer": "300000",
      "indexPrice": "0.3891840533"
    },
    {
      "marginAssets": "BNB",
      "ltv": "90.00%",
      "collateralValueRatio": "95.00%",
      "maxTransfer": "160",
      "indexPrice": "622.9584792100"
    },
    {
      "marginAssets": "DOT",
      "ltv": "90.00%",
      "collateralValueRatio": "95.00%",
      "maxTransfer": "12000",
      "indexPrice": "5.0431331628"
    },
    {
      "marginAssets": "BTC",
      "ltv": "95.00%",
      "collateralValueRatio": "95.00%",
      "maxTransfer": "10",
      "indexPrice": "90230.3058075903"
    },
    {
      "marginAssets": "ETH",
      "ltv": "95.00%",
      "collateralValueRatio": "95.00%",
      "maxTransfer": "100",
      "indexPrice": "3214.4279682820"
    }
  ]
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109500 | Account Service Unavailable, err:symbol not exist |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/trade/multiAssetsRules'
    method = "GET"
    paramsMap = {
    "timestamp": 1730863321895
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Multi-Assets Margin

**GET** `/openApi/swap/v1/user/marginAssets`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| currency | string | Margin assets, such as BTC and ETH etc. |
| totalAmount | string | Total amount of margin assets. |
| availableTransfer | string | Current available amount for transfer out, dynamic data needs to be re-queried and calculated after each transfer. |
| latestMortgageAmount | string | Latest collateral amount available. |

**Request Example**

```json
{
  "timestamp": 1730863321895
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": [
    {
      "currency": "USDC",
      "totalAmount": "0.00000000",
      "availableTransfer": "0.00000000",
      "latestMortgageAmount": "0.00000000"
    },
    {
      "currency": "USDT",
      "totalAmount": "6.89886320",
      "availableTransfer": "6.89886320",
      "latestMortgageAmount": "6.89886320"
    },
    {
      "currency": "BTC",
      "totalAmount": "6.89886320",
      "availableTransfer": "6.89886320",
      "latestMortgageAmount": "6.89886320"
    },
    {
      "currency": "ETH",
      "totalAmount": "6.89886320",
      "availableTransfer": "6.89886320",
      "latestMortgageAmount": "6.89886320"
    }
  ]
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109500 | Account Service Unavailable, err:symbol not exist |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/user/marginAssets'
    method = "GET"
    paramsMap = {
    "timestamp": 1730863321895
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### One-Click Reverse Position

**POST** `/openApi/swap/v1/trade/reverse`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| type | string | Yes | Reverse type, Reverse: immediate reverse, TriggerReverse: planned reverse |
| symbol | string | Yes | Trading pair, e.g.: BTC-USDT |
| triggerPrice | string | No | Trigger price, required for planned reverse |
| workingType | string | No | TriggerPrice price type: MARK_PRICE, CONTRACT_PRICE, INDEX_PRICE, CONTRACT_PRICE. Required for planned reverse |
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| type | string | Reverse type, Reverse: immediate reverse, TriggerReverse: planned reverse |
| positionId | string | Original position ID |
| newPositionId | string | New position ID |
| symbol | string | Trading pair, e.g.: BTC-USDT |
| positionSide | string | Position side LONG/SHORT |
| isolated | bool | Whether in isolated mode, true: isolated mode, false: cross margin |
| positionAmt | string | Position amount |
| availableAmt | string | Available amount for closing |
| unrealizedProfit | string | Unrealized profit and loss |
| realisedProfit | string | Realized profit and loss |
| initialMargin | string | Initial margin |
| margin | string | Margin |
| liquidationPrice | float64 | Liquidation price |
| avgPrice | string | Average entry price |
| leverage | int64 | Leverage |
| positionValue | string | Position value |
| markPrice | string | Mark price |
| riskRate | string | Risk rate, position will be force-reduced or liquidated when risk rate reaches 100% |
| maxMarginReduction | string | Maximum reducible margin |
| pnlRatio | string | Unrealized PNL ratio |
| updateTime | int64 | Position update time in milliseconds |

**Request Example**

```json
{
  "positionId": "1858503955839975424",
  "symbol": "BTC-USDT",
  "type": "Reverse"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "timestamp": 0,
  "data": {
    "type": "Reverse",
    "positionId": "1858503955839975424",
    "newPositionId": "1858504148832485376",
    "symbol": "BTC-USDT",
    "positionSide": "Long",
    "isolated": false,
    "positionAmt": "10000",
    "availableAmt": "10000",
    "unrealizedProfit": "4.8768",
    "realizedProfit": "-26.9683",
    "initialMargin": "8989.4302",
    "margin": "8994.3070",
    "liquidationPrice": "98138.33",
    "avgPrice": "89894.30",
    "leverage": "10X",
    "positionValue": "89899.18",
    "markPrice": "89899.1784855",
    "riskRate": "100",
    "maxMarginReduction": "0.0000",
    "pnlRatio": "0.05",
    "updateTime": "1731936893082"
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109500 | Account Service Unavailable, err:symbol not exist |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/trade/reverse'
    method = "POST"
    paramsMap = {
    "positionId": "1858503955839975424",
    "symbol": "BTC-USDT",
    "type": "Reverse"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Hedge mode Position - Automatic Margin Addition

**POST** `/openApi/swap/v1/trade/autoAddMargin`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | Trading pair, e.g., BTC-USDT, please use uppercase letters. |
| positionId | int64 | Yes | Position ID |
| functionSwitch | string | Yes | Whether to enable the automatic margin addition feature, true: enable, false: disable |
| amount | string | No | Amount of margin to be added, in USDT. Must be specified when enabling the feature. |
| timestamp | int64 | Yes | Timestamp of the request, in milliseconds. |
| recvWindow | int64 | No | Request validity window, in milliseconds. |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int64 | Error code, 0 means success, non-zero means failure |
| msg | string | Error message |
| symbol | string | Trading pair, e.g., BTC-USDT, please use uppercase letters. |
| positionId | int64 | Position ID |
| functionSwitch | string | Whether the automatic margin addition feature is enabled, true: enabled, false: disabled |
| amount | string | Amount of margin added, in USDT |

**Request Example**

```json
{
  "symbol": "BTC-USDT",
  "positionId": "1868671302923976704",
  "functionSwitch": "true",
  "amount": "130",
  "recvWindow": "10000"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "amount": 3,
  "type": 1
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/trade/autoAddMargin'
    method = "POST"
    paramsMap = {
    "symbol": "BTC-USDT",
    "positionId": "1868671302923976704",
    "functionSwitch": "true",
    "amount": "130",
    "recvWindow": "10000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Account Endpoints

#### Query account data

**GET** `/openApi/swap/v3/user/balance`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| timestamp | int64 | Yes | request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int64 | error code, 0 means successfully response, others means response failure |
| msg | string | Error Details Description |
| asset | string | user asset |
| balance | string | asset balance |
| equity | string | net asset value |
| unrealizedProfit | string | unrealized profit and loss |
| realisedProfit | string | realized profit and loss |
| availableMargin | string | available margin |
| usedMargin | string | used margin |
| freezedMargin | string | frozen margin |
| shortUid | string | short uid |

**Request Example**

```json
{}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": [
    {
      "userId": "116***295",
      "asset": "USDT",
      "balance": "194.8212",
      "equity": "196.7431",
      "unrealizedProfit": "1.9219",
      "realisedProfit": "-109.2504",
      "availableMargin": "193.7609",
      "usedMargin": "1.0602",
      "freezedMargin": "0.0000"
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v3/user/balance'
    method = "GET"
    paramsMap = {}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query position data

**GET** `/openApi/swap/v2/user/positions`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| timestamp | int64 | Yes | request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | trading pair, for example: BTC-USDT |
| positionId | string | Position ID |
| positionSide | string | position direction LONG/SHORT long/short |
| isolated | bool | Whether it is isolated margin mode, true: isolated margin mode false: cross margin |
| positionAmt | string | Position Amount |
| availableAmt | string | AvailableAmt Amount |
| unrealizedProfit | string | unrealized profit and loss |
| realisedProfit | string | realized profit and loss |
| initialMargin | string | initialMargin |
| margin | string | margin |
| liquidationPrice | float64 | Average opening price |
| avgPrice | string | liquidation price |
| leverage | int64 | leverage |
| positionValue | string | Position value |
| markPrice | string | Mark price |
| riskRate | string | Risk rate. When the risk rate reaches 100%, it will force liquidation or position reduction |
| maxMarginReduction | string | Maximum margin reduction |
| pnlRatio | string | Unrealized P&L ratio |
| updateTime | int64 | Position update time, in milliseconds timestamp. |

**Request Example**

```json
{
  "symbol": "BNB-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": [
    {
      "positionId": "1735*****52",
      "symbol": "BNB-USDT",
      "currency": "USDT",
      "positionAmt": "0.20",
      "availableAmt": "0.20",
      "positionSide": "SHORT",
      "isolated": true,
      "avgPrice": "246.43",
      "initialMargin": "9.7914",
      "leverage": 5,
      "unrealizedProfit": "-0.0653",
      "realisedProfit": "-0.0251",
      "liquidationPrice": 294.16914617776246
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/user/positions'
    method = "GET"
    paramsMap = {
    "symbol": "BNB-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Get Account Profit and Loss Fund Flow

**GET** `/openApi/swap/v2/user/income`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| incomeType | string | No | Income type, see remarks |
| startTime | int64 | No | start time |
| endTime | int64 | No | end time |
| limit | int64 | No | Number of result sets to return Default: 100 Maximum: 1000 |
| timestamp | int64 | Yes | request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | trading pair, for example: BTC-USDT |
| incomeType | string | money flow type |
| income | string | The amount of capital flow, positive numbers represent inflows, negative numbers represent outflows |
| asset | string | asset content |
| info | string | Remarks, depending on the type of stream |
| time | int64 | time, unit: millisecond |
| tranId | string | transfer id |
| tradeId | string | The original transaction ID that caused the transaction |

**Request Example**

```json
{
  "startTime": "1702713615001",
  "endTime": "1702731787011",
  "limit": "1000"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": [
    {
      "symbol": "LDO-USDT",
      "incomeType": "FUNDING_FEE",
      "income": "-0.0292",
      "asset": "USDT",
      "info": "Funding Fee",
      "time": 1702713615000,
      "tranId": "170***6*2_3*9_20***97",
      "tradeId": "170***6*2_3*9_20***97"
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/user/income'
    method = "GET"
    paramsMap = {
    "startTime": "1702713615001",
    "endTime": "1702731787011",
    "limit": "1000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Export fund flow

**GET** `/openApi/swap/v2/user/income/export`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | trading pair, for example: BTC-USDT |
| incomeType | string | No | Fund flow type, optional values:REALIZED_PNL FUNDING_FEE TRADING_FEE INSURANCE_CLEAR TRIAL_FUND ADL SYSTEM_DEDUCTION |
| startTime | int64 | No | Start time, unit: millisecond |
| endTime | int64 | No | End time, unit: millisecond |
| limit | int64 | No | Number of returned result sets default value: 100 maximum value: 1000 |
| timestamp | int64 | Yes | request timestamp, unit: millisecond |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | error msg |  |

**Request Example**

```json
{
  "endTime": "",
  "limit": "200",
  "recvWindow": "10000",
  "startTime": "",
  "symbol": "BTC-USDT"
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/user/income/export'
    method = "GET"
    paramsMap = {
    "endTime": "",
    "limit": "200",
    "recvWindow": "10000",
    "startTime": "",
    "symbol": "BTC-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Trading Commission Rate

**GET** `/openApi/swap/v2/user/commissionRate`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| timestamp | int64 | Yes | request timestamp, unit: millisecond |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| takerCommissionRate | float64 | taker fee rate |
| makerCommissionRate | float64 | maker fee rate |

**Request Example**

```json
{
  "recvWindow": "5000"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "commission": {
      "takerCommissionRate": 0.0005,
      "makerCommissionRate": 0.0002
    }
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/user/commissionRate'
    method = "GET"
    paramsMap = {
    "recvWindow": "5000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Websocket Market Data

#### Partial Order Book Depth

**Push Data Fields**

| ENV | HOST |
|---|---|

**Connection Example**

```
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "reqType": "sub",
  "dataType": "BTC-USDT@depth5@500ms"
}
```

---

#### Subscribe the Latest Trade Detail

**Push Data Fields**

| ENV | HOST |
|---|---|

**Connection Example**

```
{
  "id": "24dd0e35-56a4-4f7a-af8a-394c7060909c",
  "reqType": "sub",
  "dataType": "BTC-USDT@trade"
}
```

---

#### Subscribe K-Line Data

**Push Data Fields**

| ENV | HOST |
|---|---|

**Connection Example**

```
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "reqType": "sub",
  "dataType": "BTC-USDT@depth5@500ms"
}
```

---

#### Subscribe to 24-hour price changes

**Push Data Fields**

| ENV | HOST |
|---|---|

**Connection Example**

```
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "reqType": "sub",
  "dataType": "BTC-USDT@ticker"
}
```

---

#### Subscribe to latest price changes

**Push Data Fields**

| ENV | HOST |
|---|---|

**Connection Example**

```
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "reqType": "sub",
  "dataType": "BTC-USDT@lastPrice"
}
```

---

#### Subscribe to latest mark price changes

**Push Data Fields**

| ENV | HOST |
|---|---|

**Connection Example**

```
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "reqType": "sub",
  "dataType": "BTC-USDT@markPrice"
}
```

---

#### Subscribe to the Book Ticker Streams

**Push Data Fields**

| ENV | HOST |
|---|---|

**Connection Example**

```
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "reqType": "sub",
  "dataType": "BTC-USDT@bookTicker"
}
```

---

#### Incremental Depth Information

**Push Data Fields**

| ENV | HOST |
|---|---|

**Connection Example**

```
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "reqType": "sub",
  "dataType": "BTC-USDT@incrDepth"
}
```

---

#### Websocket Account Data

#### Order update push

WSS
Order update push
The event type of the account update event is fixed as ACCOUNT_UPDATE
When the account information changes, this event will be pushed:
This event will only be pushed when there is a change in account information (including changes in funds, positions, etc.); This event will not be pushed if the change in the order status does not cause changes in the account and positions.
Position information: push only when there is a change in the symbol position.
Fund balance changes caused by "FUNDING FEE", only push brief events:
When "FUNDING FEE" occurs in a user's cross position, the event ACCOUNT_UPDATE will only push the relevant user's asset balance information B (only push the asset balance information related to the occurrence of FUNDING FEE), and will not push any position information P.
When "FUNDING FEE" occurs in a user's isolated position, the event ACCOUNT_UPDATE will only push the relevant user asset balance information B (only push the asset balance information used by "FUNDING FEE"), and related position information P (Only the position information where this "FUNDING FEE" occurred is pushed), and the rest of the position information will not be pushed.
The field "m" represents the reason for the launch of the event, including the following possible types: DEPOSIT, WITHDRAW, ORDER, FUNDING_FEE
Account data no longer need to subscribe to channel type, after connecting wss://open-api-swap.bingx.com/swap-market?listenKey=a8ea75681542e66f1a50a1616dd06ed77dab61baa0c296bca03a9b13ee5f2dd7 , All event types will be pushed.
The effective time of the listen key is 1 hour. In order to ensure that your subscription is not interrupted, please update the listen key regularly.
subscription address
ENV	HOST
PROD
	
wss://open-api-swap.bingx.com/swap-market


VST
	
wss://vst-open-api-ws.bingx.com/swap-market
subscription parameters
subscription parameter	data type	description	values
No Data
No channel subscription required; only listenKey is needed.
data update
parameter	data type	description
s
	
string
	
Trading pair (e.g., LINK-USDT)


c
	
string
	
Client-defined order ID


i
	
int64
	
Order ID (e.g., 1627970445070303232)


S
	
string
	
Order side (BUY/SELL)


o
	
string
	
Order type (LIMIT/MARKET, etc.)


q
	
string
	
Order quantity


p
	
string
	
Order price


sp
	
string
	
Trigger price


ap
	
string
	
Average filled price


x
	
string
	
Execution type for this event (e.g., TRADE)


X
	
string
	
Current order status (NEW/PARTIALLY_FILLED/FILLED/CANCELED, etc.)


N
	
string
	
Fee asset (e.g., USDT)


n
	
string
	
Fee (may be negative)


T
	
int64
	
Trade time (timestamp in ms)


wt
	
string
	
Trigger price type: MARK_PRICE / CONTRACT_PRICE / INDEX_PRICE


ps
	
string
	
Position side: LONG / SHORT / BOTH


rp
	
string
	
Realized PnL for this trade


z
	
string
	
Cumulative filled quantity


sg
	
boolean
	
Guaranteed TP/SL enabled: true/false


ti
	
int64
	
Related conditional order ID (e.g., 1771124709866754048)


ro
	
boolean
	
Reduce-only order flag


td
	
string
	
Trade ID


tv
	
string
	
Trade value / notional

No channel subscription required; only listenKey is needed.

subscribe sample
Copy Code
{}
subscribe success sample
Copy Code
{
  "code": 0,
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "msg": "SUCCESS",
  "timestamp": 1759980142604
}
data update sample
Copy Code
{
  "e": "TRADE_UPDATE",
  "E": 1758608899350,
  "T": 1758608899316,  // Trade time (timestamp in ms)
  "o": {
      "s": "BTC-USDT",  // Trading pair (e.g., LINK-USDT)
      "c": "",  // Client-defined order ID
      "i": 1970374651259388000,  // Order ID (e.g., 1627970445070303232)
      "S": "SELL",  // Order side (BUY/SELL)
      "o": "MARKET",  // Order type (LIMIT/MARKET, etc.)
      "q": "0.00100000",  // Order quantity
      "p": "112848.10000000",  // Order price
      "sp": "0.00000000",  // Trigger price
      "ap": "112848.10000000",  // Average filled price
      "x": "TRADE",  // Execution type for this event (e.g., TRADE)
      "X": "FILLED",  // Current order status (NEW/PARTIALLY_FILLED/FILLED/CANCELED, etc.)
      "N": "USDT",  // Fee asset (e.g., USDT)
      "n": "-0.05642405",  // Fee (may be negative)
      "T": 1758608899316,  // Trade time (timestamp in ms)
      "wt": "",  // Trigger price type: MARK_PRICE / CONTRACT_PRICE / INDEX_PRICE
      "ps": "SHORT",  // Position side: LONG / SHORT / BOTH
      "rp": "0.00000000",  // Realized PnL for this trade
      "z": "0.00100000",  // Cumulative filled quantity
      "sg": "false",  // Guaranteed TP/SL enabled: true/false
      "ti": 0,  // Related conditional order ID (e.g., 1771124709866754048)
      "ro": false,  // Reduce-only order flag
      "td": 511178071,  // Trade ID
      "tv": "112.8"  // Trade value / notional
    }  // Order type (LIMIT/MARKET, etc.)
}
cancel subscribe sample
Copy Code
{}
error code
error code	error message
403
	
Internal service call exception


1006
	
Internal service call exception.Generally network related issue


80015
	
dataType not supported
code demo
PythonGolangNodejsJavaC#PHP
Copy Code
                      
import json
import websocket
import gzip
import io
URL="wss://open-api-swap.bingx.com/swap-market" 
CHANNEL= {}
class Test(object):

    def __init__(self):
        self.url = URL 
        self.ws = None

    def on_open(self, ws):
        print('WebSocket connected')
                subStr = json.dumps(CHANNEL)
        ws.send(subStr)
        print("Subscribed to :",subStr)
        
    def on_data(self, ws, string, type, continue_flag):
        compressed_data = gzip.GzipFile(fileobj=io.BytesIO(string), mode='rb')
        decompressed_data = compressed_data.read()
        utf8_data = decompressed_data.decode('utf-8')
        print(utf8_data)

    def on_message(self, ws, message):
        compressed_data = gzip.GzipFile(fileobj=io.BytesIO(message), mode='rb')
        decompressed_data = compressed_data.read()
        utf8_data = decompressed_data.decode('utf-8')
        print(utf8_data)  #this is the message you need 
        if utf8_data == "Ping": # this is very important , if you receive 'Ping' you need to send 'Pong' 
           ws.send("Pong")

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws, close_status_code, close_msg):
        print('The connection is closed!')

    def start(self):
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self.on_open,
            on_message=self.on_message,
            # on_data=self.on_data,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        self.ws.run_forever()


if __name__ == "__main__":
    test = Test()
    test.start()
                  
Subscription Address
Subscription Parameters
Data Update
Subscribe Sample
Subscribe Success Sample
Data Update Sample
Cancel Subscribe Sample
Error Code
Code Demo

---

#### Account balance and position update push

WSS
Account balance and position update push
This type of event will be pushed when a new order is created, an order has a new deal, or a new status change. The event type is unified as ORDER_TRADE_UPDATE.
Order direction
BUY buy
SELL sell
Order Type
MARKET market order
TAKE_PROFIT_MARKET take profit market order
STOP_MARKET stop market order
LIMIT limit order
TAKE_PROFIT take profit limit order
STOP stop limit order
TRIGGER_MARKET stop market order with trigger
TRIGGER_LIMIT stop limit order with trigger
TRAILING_STOP_MARKET trailing stop market order
TRAILING_TP_SL trailing take profit or stop loss
LIQUIDATION strong liquidation order
The specific execution type of this event
NEW
CANCELED removed
CALCULATED order ADL or liquidation
EXPIRED order lapsed
TRADE transaction
Order Status
NEW
PARTIALLY_FILLED
FILLED
CANCELED
EXPIRED
Account data no longer need to subscribe to channel type, after connect wss://open-api-swap.bingx.com/swap-market?listenKey=a8ea75681542e66f1a50a1616dd06ed77dab61baa0c296bca03a9b13ee5f2dd7 , All event types will be pushed.
The effective time of the listen key is 1 hour. In order to ensure that your subscription is not interrupted, please update the listen key regularly.
subscription address
ENV	HOST
PROD
	
wss://open-api-swap.bingx.com/swap-market


VST
	
wss://vst-open-api-ws.bingx.com/swap-market
subscription parameters
subscription parameter	data type	description	values
No Data
No channel subscription required; only listenKey is needed.
data update
parameter	data type	description
e
	
string
	
Event type (ACCOUNT_UPDATE)


E
	
int64
	
Event time in milliseconds


T
	
int64
	
Push time in milliseconds


a
	
object
	
Account update event object


a.m
	
string
	
Reason for the account update


a.B
	
array
	
Balance information array


a.B.a
	
string
	
Asset name (e.g. USDT)


a.B.wb
	
string
	
Wallet balance


a.B.cw
	
string
	
Wallet balance excluding isolated margin


a.B.bc
	
string
	
Balance change


a.P
	
array
	
Position information array


a.P.s
	
string
	
Trading pair (e.g. LINK-USDT)


a.P.pa
	
string
	
Position amount


a.P.ep
	
string
	
Entry price


a.P.up
	
string
	
Unrealized profit and loss


a.P.mt
	
string
	
Margin mode (isolated / crossed)


a.P.iw
	
string
	
Isolated position margin


a.P.ps
	
string
	
Position side (LONG / SHORT / BOTH)


a.P.cr
	
string
	
Realized profit and loss

No channel subscription required; only listenKey is needed.

subscribe sample
Copy Code
{}
subscribe success sample
Copy Code
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "code": 0,
  "msg": "",
  "dataType": "",
  "data": null
}
data update sample
Copy Code
{
  "e": "ACCOUNT_UPDATE",  // Event type (ACCOUNT_UPDATE)
  "E": 1758608899352,  // Event time in milliseconds
  "a": {
      "m": "ORDER",  // Reason for the account update
      "B": [
            {
              "a": "USDT",  // Asset name (e.g. USDT)
              "wb": "117.80007595",  // Wallet balance
              "cw": "95.23045595",  // Wallet balance excluding isolated margin
              "bc": "0"  // Balance change
            }
          ],  // Balance information array
      "P": [
            {
              "s": "BTC-USDT",  // Trading pair (e.g. LINK-USDT)
              "pa": "0.00100000",  // Position amount
              "ep": "112848.10000000",  // Entry price
              "up": "-0.00004435",  // Unrealized profit and loss
              "mt": "cross",  // Margin mode (isolated / crossed)
              "iw": "22.56957565",  // Isolated position margin
              "ps": "SHORT",  // Position side (LONG / SHORT / BOTH)
              "cr": "-0.05642405"  // Realized profit and loss
            }
          ]  // Position information array
    }  // Account update event object
}
cancel subscribe sample
Copy Code
{}
error code
error code	error message
403
	
Internal service call exception


1006
	
Internal service call exception.Generally network related issue


80015
	
dataType not supported
code demo
PythonGolangNodejsJavaC#PHP
Copy Code
                      
import json
import websocket
import gzip
import io
URL="wss://open-api-swap.bingx.com/swap-market?listenKey=a8ea75681542e66f1a50a1616dd06ed77dab61baa0c296bca03a9b13ee5f2dd7" 

class Test(object):

    def __init__(self):
        self.url = URL 
        self.ws = None

    def on_open(self, ws):
        print('WebSocket connected')
        

    def on_data(self, ws, string, type, continue_flag):
        compressed_data = gzip.GzipFile(fileobj=io.BytesIO(string), mode='rb')
        decompressed_data = compressed_data.read()
        utf8_data = decompressed_data.decode('utf-8')
        print(utf8_data)

    def on_message(self, ws, message):
        compressed_data = gzip.GzipFile(fileobj=io.BytesIO(message), mode='rb')
        decompressed_data = compressed_data.read()
        utf8_data = decompressed_data.decode('utf-8')
        print(utf8_data)  #this is the message you need 
        if utf8_data == "Ping": # this is very important , if you receive 'Ping' you need to send 'Pong' 
           ws.send("Pong")

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws, close_status_code, close_msg):
        print('The connection is closed!')

    def start(self):
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self.on_open,
            on_message=self.on_message,
            # on_data=self.on_data,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        self.ws.run_forever()


if __name__ == "__main__":
    test = Test()
    test.start()
                  
Subscription Address
Subscription Parameters
Data Update
Subscribe Sample
Subscribe Success Sample
Data Update Sample
Cancel Subscribe Sample
Error Code
Code Demo

---

#### Configuration updates such as leverage and margin mode

WSS
Configuration updates such as leverage and margin mode
When the account configuration changes, the event type will be pushed as ACCOUNT_CONFIG_UPDATE
When the leverage of a trading pair changes, the push message will contain the object ac, which represents the account configuration of the trading pair, where s represents the specific trading pair, l represents the leverage of long positions, S represents the leverage of short positions, and mt represents the margin mode.
For more about return error codes, please see the error code description on the homepage.
Each time a connection is successfully established, a full data push will occur once, followed by another full push every 5 seconds.
Account data no longer need to subscribe to channel type, after connecting wss://open-api-swap.bingx.com/swap-market?listenKey=a8ea75681542e66f1a50a1616dd06ed77dab61baa0c296bca03a9b13ee5f2dd7, All event types will be pushed.
The effective time of the listen key is 1 hour. In order to ensure that your subscription is not interrupted, please update the listen key regularly.
subscription address
ENV	HOST
PROD
	
wss://open-api-swap.bingx.com/swap-market


VST
	
wss://vst-open-api-ws.bingx.com/swap-market
subscription parameters
subscription parameter	data type	description	values
No Data
No channel subscription required; only listenKey is needed.
data update
parameter	data type	description
e
	
string
	
Event type (ACCOUNT_CONFIG_UPDATE)


E
	
int64
	
Event time in milliseconds


ac
	
object
	
Account configuration update object


s
	
string
	
Trading pair (e.g. BTC-USDT)


l
	
int32
	
Long position leverage


S
	
int32
	
Short position leverage


mt
	
string
	
Margin mode (cross / isolated)

No channel subscription required; only listenKey is needed.

subscribe sample
Copy Code
{}
subscribe success sample
Copy Code
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "code": 0,
  "msg": "",
  "dataType": "",
  "data": null
}
data update sample
Copy Code
{
  "e": "ACCOUNT_CONFIG_UPDATE",  // Event type (ACCOUNT_CONFIG_UPDATE)
  "E": 1769443029713,  // Event time in milliseconds
  "ac": {
      "s": "NCCOGOLD2USD-USDT",  // Trading pair (e.g. BTC-USDT)
      "l": 412,  // Long position leverage
      "S": 428,  // Short position leverage
      "mt": "cross"  // Margin mode (cross / isolated)
    }  // Account configuration update object
}
cancel subscribe sample
Copy Code
{}
error code
error code	error message
403
	
Internal service call exception


1006
	
Internal service call exception.Generally network related issue


80015
	
dataType not supported
code demo
PythonGolangNodejsJavaC#PHP
Copy Code
                      
import json
import websocket
import gzip
import io
URL="wss://open-api-swap.bingx.com/swap-market" 
CHANNEL= {}
class Test(object):

    def __init__(self):
        self.url = URL 
        self.ws = None

    def on_open(self, ws):
        print('WebSocket connected')
                subStr = json.dumps(CHANNEL)
        ws.send(subStr)
        print("Subscribed to :",subStr)
        
    def on_data(self, ws, string, type, continue_flag):
        compressed_data = gzip.GzipFile(fileobj=io.BytesIO(string), mode='rb')
        decompressed_data = compressed_data.read()
        utf8_data = decompressed_data.decode('utf-8')
        print(utf8_data)

    def on_message(self, ws, message):
        compressed_data = gzip.GzipFile(fileobj=io.BytesIO(message), mode='rb')
        decompressed_data = compressed_data.read()
        utf8_data = decompressed_data.decode('utf-8')
        print(utf8_data)  #this is the message you need 
        if utf8_data == "Ping": # this is very important , if you receive 'Ping' you need to send 'Pong' 
           ws.send("Pong")

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws, close_status_code, close_msg):
        print('The connection is closed!')

    def start(self):
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self.on_open,
            on_message=self.on_message,
            # on_data=self.on_data,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        self.ws.run_forever()


if __name__ == "__main__":
    test = Test()
    test.start()
                  
Subscription Address
Subscription Parameters
Data Update
Subscribe Sample
Subscribe Success Sample
Data Update Sample
Cancel Subscribe Sample
Error Code
Code Demo

---

### Spot

#### Market Data

#### Spot trading symbols

**GET** `/openApi/spot/v1/common/symbols`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | Trading pair, e.g., BTC-USDT |
| timestamp | int64 | Yes | Timestamp of initiating the request, Unit: milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | Trading symbol |
| tickSize | float64 | Price tick size |
| stepSize | float64 | Quantity step size |
| minQty | float64 | Deprecated; can be calculated using minQty=minNotional/price |
| maxQty | float64 | Deprecated; can be calculated using maxQty=maxNotional/price |
| minNotional | float64 | Minimum trading notional |
| maxNotional | float64 | Maximum trading notional |
| maxMarketNotional | float64 | Maximum notional amount allowed for a single market order |
| status | int64 | 0 offline, 1 online, 5 pre-open, 10 accessed, 25 suspended, 29 pre-delisted, 30 delisted |
| apiStateBuy | boolean | Buy allowed |
| apiStateSell | boolean | Sell allowed |
| timeOnline | long | Symbol online time |
| offTime | long | Symbol offline time |
| maintainTime | long | Symbol maintenance time |
| displayName | string | Display name for UI |

**Request Example**

```json
{
  "symbol": "BTC-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "debugMsg": "",
  "data": {
    "symbols": [
      {
        "symbol": "BTC-USDT",
        "minQty": 0.0001826,
        "maxQty": 18.2663756,
        "minNotional": 5,
        "maxNotional": 500000,
        "maxMarketNotional": 500000,
        "status": 1,
        "tickSize": 0.01,
        "stepSize": 0.00001
      }
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/spot/v1/common/symbols'
    method = "GET"
    paramsMap = {
    "symbol": "BTC-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Recent Trades List

**GET** `/openApi/swap/v2/quote/trades`

---

#### Order Book

**GET** `/openApi/swap/v2/quote/depth`

---

#### Kline/Candlestick Data

**GET** `/openApi/swap/v3/quote/klines`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| interval | string | Yes | time interval, refer to field description |
| startTime | int64 | No | Start time, unit: millisecond |
| endTime | int64 | No | End time, unit: millisecond |
| timeZone | int32 | No | Time zone offset, only supports 0 or 8 (UTC+0 or UTC+8) |
| limit | int64 | No | default: 500 maximum: 1440 |
| timestamp | int64 | Yes | Timestamp of initiating the request, Unit: milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| open | float64 | Opening Price |
| close | float64 | Closing Price |
| high | float64 | High Price |
| low | float64 | Low Price |
| volume | float64 | transaction volume |
| time | int64 | k-line time stamp, unit milliseconds |

**Request Example**

```json
{
  "symbol": "KNC-USDT",
  "interval": "1h",
  "timeZone": 8,
  "limit": "1000",
  "startTime": "1702717199998"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": [
    {
      "open": "0.7034",
      "close": "0.7065",
      "high": "0.7081",
      "low": "0.7033",
      "volume": "635494.00",
      "time": 1702717200000
    }
  ]
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109425 | Trading pair does not exist |
| 100410 | rate limited |
| 109415 | Trading pair is suspended |
| 109400 | Invalid parameters |
| 109429 | Too many invalid requests |
| 109419 | Trading pair not supported |
| 109701 | Network issue |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v3/quote/klines'
    method = "GET"
    paramsMap = {
    "symbol": "KNC-USDT",
    "interval": "1h",
    "timeZone": 8,
    "limit": "1000",
    "startTime": "1702717199998"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### 24hr Ticker Price Change Statistics

**GET** `/openApi/swap/v2/quote/ticker`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| timestamp | int64 | Yes | Timestamp of initiating the request, Unit: milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | trading pair, for example: BTC-USDT |
| priceChange | string | 24 hour price change |
| priceChangePercent | string | price change percentage |
| lastPrice | string | latest transaction price |
| lastQty | string | latest transaction amount |
| highPrice | string | 24-hour highest price |
| lowPrice | string | 24 hours lowest price |
| volume | string | 24-hour volume |
| quoteVolume | string | 24-hour turnover, the unit is USDT |
| openPrice | string | first price within 24 hours |
| openTime | int64 | The time when the first transaction occurred within 24 hours |
| closeTime | int64 | The time when the last transaction occurred within 24 hours |
| bidPrice | float64 | bid price |
| bidQty | float64 | bid quantity |
| askPrice | float64 | ask price |
| askQty | float64 | ask quantity |

**Request Example**

```json
{
  "symbol": "SFP-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "symbol": "SFP-USDT",
    "priceChange": "0.0295",
    "priceChangePercent": "4.15",
    "lastPrice": "0.7409",
    "lastQty": "10",
    "highPrice": "0.7506",
    "lowPrice": "0.6903",
    "volume": "4308212",
    "quoteVolume": "3085449.53",
    "openPrice": "0.7114",
    "openTime": 1702719833853,
    "closeTime": 1702719798603,
    "askPrice": "0.7414",
    "askQty": "99",
    "bidPrice": "0.7413",
    "bidQty": "84"
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109425 | Trading pair does not exist |
| 100410 | rate limited |
| 109400 | Invalid parameters |
| 109415 | Trading pair is suspended |
| 109429 | Too many invalid requests |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/quote/ticker'
    method = "GET"
    paramsMap = {
    "symbol": "SFP-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Order Book aggregation

**GET** `/openApi/spot/v2/market/depth`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | Trading pair, such as: BTC-USDT |
| depth | int64 | Yes | Query depth |
| type | string | Yes | step0 default precision, step1 to step5 are 10 to 100000 times precision respectively |

**Response Body**

| filed | data type | description |
|---|---|---|
| bids | array | Buy depth, where the first element of the array is the price and the second element is the quantity |
| asks | array | Sell depth, where the first element of the array is the price and the second element is the quantity |
| ts | int64 | Timestamp |

**Request Example**

```json
{
  "symbol": "BTC-USDT",
  "limit": 20,
  "type": "step0"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1707143021361,
  "data": {
    "bids": [
      [
        "43340.92",
        "1.91154"
      ],
      [
        "43340.88",
        "3.85804"
      ],
      [
        "43340.85",
        "4.26840"
      ],
      [
        "43340.83",
        "2.08925"
      ],
      [
        "43340.81",
        "2.04579"
      ],
      [
        "43340.79",
        "1.58294"
      ],
      [
        "43340.77",
        "1.54605"
      ],
      [
        "43340.76",
        "2.11097"
      ],
      [
        "43340.74",
        "1.82713"
      ],
      [
        "43340.72",
        "1.97847"
      ],
      [
        "43340.69",
        "3.12035"
      ],
      [
        "43340.65",
        "3.49761"
      ],
      [
        "43340.61",
        "3.61076"
      ],
      [
        "43340.56",
        "4.56538"
      ],
      [
        "43340.47",
        "4.3701"
      ],
      [
        "43340.46",
        "3.47356"
      ],
      [
        "43340.44",
        "10.99309"
      ],
      [
        "43340.23",
        "9.78746"
      ],
      [
        "43339.90",
        "9.77564"
      ],
      [
        "43339.86",
        "11.06385"
      ]
    ],
    "asks": [
      [
        "43341.79",
        "5.76033"
      ],
      [
        "43341.86",
        "3.9063"
      ],
      [
        "43341.88",
        "5.76033"
      ],
      [
        "43341.90",
        "4.98845"
      ],
      [
        "43341.92",
        "4.98845"
      ],
      [
        "43341.94",
        "5.25236"
      ],
      [
        "43341.95",
        "22.48145"
      ],
      [
        "43341.98",
        "9.40042"
      ],
      [
        "43342.00",
        "13.58550"
      ],
      [
        "43342.02",
        "9.44509"
      ],
      [
        "43342.05",
        "5.25236"
      ],
      [
        "43342.07",
        "4.83999"
      ],
      [
        "43342.08",
        "4.74583"
      ],
      [
        "43342.10",
        "4.58787"
      ],
      [
        "43342.11",
        "5.61344"
      ],
      [
        "43342.13",
        "4.57564"
      ],
      [
        "43342.15",
        "5.14039"
      ],
      [
        "43342.17",
        "4.65339"
      ],
      [
        "43342.19",
        "5.32833"
      ],
      [
        "43342.22",
        "9.74216"
      ]
    ],
    "ts": 1707143021361
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/spot/v2/market/depth'
    method = "GET"
    paramsMap = {
    "symbol": "BTC-USDT",
    "limit": 20,
    "type": "step0"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Symbol Price Ticker

**GET** `/openApi/swap/v1/ticker/price`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT,If no transaction pair parameters are sent, all transaction pair information will be returned |
| timestamp | int64 | Yes | Timestamp of initiating the request, Unit: milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | trading pair, for example: BTC-USDT |
| price | string | price |
| time | int64 | matching engine time |

**Request Example**

```json
{
  "symbol": "TIA-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "symbol": "TIA-USDT",
    "price": "14.0658",
    "time": 1702718922941
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109425 | Trading pair does not exist |
| 109400 | Invalid parameters |
| 109415 | Trading pair is suspended |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v1/ticker/price'
    method = "GET"
    paramsMap = {
    "symbol": "TIA-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Symbol Order Book Ticker

**GET** `/openApi/swap/v2/quote/bookTicker`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| timestamp | int64 | Yes | Timestamp of initiating the request, Unit: milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| bid_price | float64 | Optimal purchase price |
| bid_qty | float64 | Order quantity |
| ask_price | float64 | Best selling price |
| lastUpdateId | int64 | The ID of the latest trade |
| time | long | The time of the trade in milliseconds |
| ask_qty | float64 | Order quantity |

**Request Example**

```json
{
  "symbol": "BTC-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "book_ticker": {
      "symbol": "BTC-USDT",
      "bid_price": 42211.1,
      "bid_qty": 12663,
      "ask_price": 42211.8,
      "ask_qty": 128854
    }
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109425 | Trading pair does not exist |
| 109400 | Invalid parameters |
| 109415 | Trading pair is suspended |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/quote/bookTicker'
    method = "GET"
    paramsMap = {
    "symbol": "BTC-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Historical K-line

**GET** `/openApi/market/his/v1/kline`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | Trading pair, e.g., BTC-USDT, please use uppercase letters |
| interval | string | Yes | Time interval, reference field description |
| startTime | int64 | No | Start time, unit: milliseconds |
| endTime | int64 | No | End time, unit: milliseconds |
| limit | int64 | No | Default value: 500 Maximum value: 500 |

**Response Body**

| filed | data type | description |
|---|---|---|
| klines | array | K-line array |

**Request Example**

```json
{
  "symbol": "BTC-USDT",
  "interval": "1m",
  "limit": 5
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1702720626772,
  "data": [
    [
      1702720620000,
      42216.29,
      42216.94,
      42216.29,
      42216.72,
      0.2,
      1702720679999,
      8548.46
    ],
    [
      1702720560000,
      42220.61,
      42221.1,
      42215.56,
      42216.63,
      2.93,
      1702720619999,
      123968.7
    ],
    [
      1702720500000,
      42182.59,
      42220.38,
      42182.59,
      42220.38,
      1.53,
      1702720559999,
      64851.33
    ],
    [
      1702720440000,
      42182.84,
      42183.16,
      42182.22,
      42182.81,
      2.54,
      1702720499999,
      107559.45
    ],
    [
      1702720380000,
      42199.72,
      42204.53,
      42180.2,
      42182.76,
      1.1,
      1702720439999,
      46549.09
    ]
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/market/his/v1/kline'
    method = "GET"
    paramsMap = {
    "symbol": "BTC-USDT",
    "interval": "1m",
    "limit": 5
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Old Trade Lookup

**GET** `/openApi/market/his/v1/trade`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | Trading pair, e.g., BTC-USDT, please use uppercase letters |
| limit | int64 | No | Default 100, maximum 500 |
| fromId | string | No | The last recorded tid |

**Response Body**

| filed | data type | description |
|---|---|---|
| id | long | Trade id |
| price | float64 | Price |
| qty | float64 | Quantity |
| time | long | Time |
| buyerMaker | boolean | Buyer maker |

**Request Example**

```json
{
  "symbol": "BTC-USDT",
  "limit": 5
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1702720325973,
  "data": [
    {
      "tid": "170891918044290305561",
      "t": 1708919180442,
      "ms": 2,
      "s": "BTC-USDT",
      "p": 51496.35,
      "v": 0.00063
    },
    {
      "tid": "170891917959890305560",
      "t": 1708919179598,
      "ms": 1,
      "s": "BTC-USDT",
      "p": 51495.89,
      "v": 0.00188
    },
    {
      "tid": "170891917942490305559",
      "t": 1708919179424,
      "ms": 1,
      "s": "BTC-USDT",
      "p": 51496.159,
      "v": 0.00075
    },
    {
      "tid": "170891917907790305558",
      "t": 1708919179077,
      "ms": 2,
      "s": "BTC-USDT",
      "p": 51496.13,
      "v": 0.01044
    },
    {
      "tid": "170891917896690305557",
      "t": 1708919178966,
      "ms": 1,
      "s": "BTC-USDT",
      "p": 51496,
      "v": 0.00129
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/market/his/v1/trade'
    method = "GET"
    paramsMap = {
    "symbol": "BTC-USDT",
    "limit": 5
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Account Endpoints

#### Query Assets

**GET** `/openApi/spot/v1/account/balance`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| recvWindow | int64 | No | Timestamp of initiating the request, Unit: milliseconds |
| timestamp | int64 | Yes | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| balances | Array | Asset list, element fields refer to the following table |

**Request Example**

```json
{
  "recvWindow": "60000"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "debugMsg": "",
  "data": {
    "balances": [
      {
        "asset": "USDT",
        "free": "566773.193402631",
        "locked": "244.18616265388994"
      },
      {
        "asset": "CHEEMS",
        "free": "294854132046232",
        "locked": "18350553840"
      },
      {
        "asset": "VST",
        "free": "0",
        "locked": "0"
      }
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/spot/v1/account/balance'
    method = "GET"
    paramsMap = {
    "recvWindow": "60000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Asset transfer records

**GET** `/openApi/api/v3/asset/transfer`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| type | ENUM | Yes | transfer type, (query by type or tranId) |
| tranId | LONG | No | transaction ID, (query by type or tranId) |
| startTime | LONG | No | Starting time1658748648396 |
| endTime | LONG | No | End Time 1658748648396 |
| current | int64 | No | current page default1 |
| size | int64 | No | Page size default 10 can not exceed 100 |
| recvWindow | LONG | No | Execution window time, cannot be greater than 60000 |
| timestamp | LONG | Yes | current timestamp e.g.1658748648396 |

**Response Body**

| filed | data type | description |
|---|---|---|
| total | LONG | total |
| rows | Array | Array |
| asset | string | coin name |
| amount | DECIMAL | coin amount |
| type | ENUM | transfer tpye |
| status | string | CONFIRMED |
| tranId | LONG | Transaction ID |
| timestamp | LONG | Transfer time stamp |

**Request Example**

```json
{
  "type": "FUND_PFUTURES"
}
```

**Response Example**

```json
{
  "total": 2,
  "rows": [
    {
      "asset": "VST",
      "amount": "100000.00000000000000000000",
      "type": "FUND_PFUTURES",
      "status": "CONFIRMED",
      "tranId": 37600111,
      "timestamp": 1702252271000
    },
    {
      "asset": "USDT",
      "amount": "2218.72352626000000000000",
      "type": "FUND_PFUTURES",
      "status": "CONFIRMED",
      "tranId": 37600222,
      "timestamp": 1702351131000
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/api/v3/asset/transfer'
    method = "GET"
    paramsMap = {
    "type": "FUND_PFUTURES"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Main Accoun internal transfer

**POST** `/openApi/wallets/v1/capital/innerTransfer/apply`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| coin | string | Yes | Name of the transferred currency |
| userAccountType | int64 | Yes | User account type 1=UID 2=phone number 3=email |
| userAccount | string | Yes | User account: UID, phone number, email |
| amount | float64 | Yes | Transfer amount |
| callingCode | string | No | Area code for telephone, required when userAccountType=2. |
| walletType | int64 | Yes | Account type, 1 Fund Account; 2 Standard Futures Account; 3 Perpetual Futures Account; 4 Spot Account |
| transferClientId | string | No | Custom ID for internal transfer by the client, combination of numbers and letters, length less than 100 characters |
| timestamp | int64 | Yes | The timestamp of the request, in milliseconds. |
| recvWindow | int64 | No | Request validity time window, unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| id | string | The platform returns the unique ID of the internal transfer record. |
| transferClientId | string | Custom ID for internal transfer by the client, combination of numbers and letters, length less than 100 characters |

**Request Example**

```json
{
  "amount": "10.0",
  "coin": "USDT",
  "userAccount": "16779999",
  "userAccountType": "1",
  "walletType": "1"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1702558152381,
  "data": {
    "id": "12******1"
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/wallets/v1/capital/innerTransfer/apply'
    method = "POST"
    paramsMap = {
    "amount": "10.0",
    "coin": "USDT",
    "userAccount": "16779999",
    "userAccountType": "1",
    "walletType": "1"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Asset Transfer New

**POST** `/openApi/api/asset/v1/transfer`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| fromAccount | string | Yes | fromAccount, fund：Funding Account spot:Spot Account, stdFutures:Standard Contract, coinMPerp:COIN-M Perpetual Future, USDTMPerp:Perpetual Future |
| toAccount | string | Yes | toAccount, fund:Funding Account spot:Spot Account, stdFutures:Standard Contract, coinMPerp:COIN-M Perpetual Future, USDTMPerp:Perpetual Future |
| asset | string | Yes | coin name e.g. USDT |
| amount | DECIMAL | Yes | amount |
| recvWindow | LONG | No | Execution window time, cannot be greater than 60000 |
| timestamp | LONG | Yes | current timestamp e.g. 1658748648396 |

**Response Body**

| filed | data type | description |
|---|---|---|
| transferId | string | transfer ID |

**Request Example**

```json
{
  "recvWindow": "6000",
  "asset": "USDT",
  "amount": "1095",
  "fromAccount": "fund",
  "toAccount": "spot"
}
```

**Response Example**

```json
{
  "transferId": "17********28"
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/api/asset/v1/transfer'
    method = "POST"
    paramsMap = {
    "recvWindow": "6000",
    "asset": "USDT",
    "amount": "1095",
    "fromAccount": "fund",
    "toAccount": "spot"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query transferable currency

**GET** `/openApi/api/asset/v1/transfer/supportCoins`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| fromAccount | string | Yes | fromAccount, fund：Funding Account spot:Spot Account, stdFutures:Standard Contract, coinMPerp:COIN-M Perpetual Future, USDTMPerp:Perpetual Future |
| toAccount | string | Yes | toAccount, fund:Funding Account spot:Spot Account, stdFutures:Standard Contract, coinMPerp:COIN-M Perpetual Future, USDTMPerp:Perpetual Future |
| recvWindow | int64 | No | Execution window time, cannot be greater than 60000 |
| timestamp | int64 | Yes | Current timestamp e.g. 1658748648396 |

**Response Body**

| filed | data type | description |
|---|---|---|
| coins | Array | Coin Asset, element fields refer to the following table |

**Request Example**

```json
{
  "fromAccount": "spot",
  "toAccount": "fund",
  "recvWindow": "60000"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "debugMsg": "",
  "data": {
    "coins": [
      {
        "asset": "USDT",
        "amount": "566773.193402631"
      },
      {
        "asset": "CHEEMS",
        "amount": "24324.21"
      }
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/api/asset/v1/transfer/supportCoins'
    method = "GET"
    paramsMap = {
    "fromAccount": "spot",
    "toAccount": "fund",
    "recvWindow": "60000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Asset transfer records new

**GET** `/openApi/api/v3/asset/transferRecord`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| fromAccount | string | Yes | fromAccount, fund：Funding Account spot:Spot Account, stdFutures:Standard Contract, coinMPerp:COIN-M Perpetual Future, USDTMPerp:Perpetual Future |
| toAccount | string | Yes | toAccount, fund:Funding Account spot:Spot Account, stdFutures:Standard Contract, coinMPerp:COIN-M Perpetual Future, USDTMPerp:Perpetual Future |
| tranId | LONG | No | transaction ID, (query by fromAccount|toAccount or transferId) |
| startTime | LONG | No | Starting time1658748648396 |
| endTime | LONG | No | End Time 1658748648396 |
| pageIndex | int64 | No | current page default1 |
| pageSize | int64 | No | Page size default 10 can not exceed 100 |
| recvWindow | LONG | No | Execution window time, cannot be greater than 60000 |
| timestamp | LONG | Yes | current timestamp e.g.1658748648396 |

**Response Body**

| filed | data type | description |
|---|---|---|
| transferId | string | transferId |
| asset | string | Coin Name |
| amount | DECIMAL | Transfer Amount |
| fromAccount | string | fromAccount, fund：Funding Account spot:Spot Account, stdFutures:Standard Contract, coinMPerp:COIN-M Perpetual Future, USDTMPerp:Perpetual Future |
| toAccount | string | toAccount, fund：Funding Account spot:Spot Account, stdFutures:Standard Contract, coinMPerp:COIN-M Perpetual Future, USDTMPerp:Perpetual Future |
| timestamp | LONG | Transfer time stamp |

**Request Example**

```json
{
  "fromAccount": "fund",
  "toAccount": "spot"
}
```

**Response Example**

```json
{
  "total": 2,
  "rows": [
    {
      "asset": "VST",
      "amount": "100000.00000000000000000000",
      "status": "CONFIRMED",
      "transferId": "37600111",
      "timestamp": 1702252271000,
      "fromAccount": "fund",
      "toAccount": "spot"
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/api/v3/asset/transferRecord'
    method = "GET"
    paramsMap = {
    "fromAccount": "fund",
    "toAccount": "spot"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Fund Account Assets

**GET** `/openApi/fund/v1/account/balance`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| asset | string | No | Coin name, return all when not transmitted |
| recvWindow | int64 | No | Timestamp of initiating the request, Unit: milliseconds |
| timestamp | int64 | Yes | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| balances | Array | Asset list, element fields refer to the following table |

**Request Example**

```json
{
  "asset": "USDT",
  "recvWindow": "60000"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "debugMsg": "",
  "data": {
    "balances": [
      {
        "asset": "USDT",
        "free": "566773.193402631",
        "locked": "244.18616265388994"
      },
      {
        "asset": "CHEEMS",
        "free": "294854132046232",
        "locked": "18350553840"
      },
      {
        "asset": "VST",
        "free": "0",
        "locked": "0"
      }
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/fund/v1/account/balance'
    method = "GET"
    paramsMap = {
    "asset": "USDT",
    "recvWindow": "60000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Main account internal transfer records

**GET** `/openApi/wallets/v1/capital/innerTransfer/records`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| coin | string | Yes | Transfer coin name |
| transferClientId | string | No | Client's self-defined internal transfer ID. When both platform ID and transferClientId are provided as input, the query will be based on the platform ID. |
| startTime | long | No | Start time |
| endTime | long | No | End time |
| offset | int64 | No | Starting record number, default is 0 |
| limit | int64 | No | Page size, default is 100, maximum is 1000 |
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| data | object | Inner transfer records list |
| total | int64 | Total number of addresses |
| id | long | Inner transfer ID |
| coin | string | Coin name |
| receiver | long | Receiver UID |
| amount | decimal | Transfer amount |
| time | long | Internal transfer time |
| status | Integer | Status 4-Pending review 5-Failed 6-Completed |
| transferClientId | string | Client's self-defined internal transfer ID. When both platform ID and transferClientId are provided as input, the query will be based on the platform ID. |
| fromUid | long | Payer's account |
| recordType | string | Out: transfer out record, in: transfer in record |

**Request Example**

```json
{
  "recvWindow": "30000",
  "limit": "1000",
  "coin": "BTC",
  "startTime": "1701519898118",
  "endTime": "1702383898118"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1702383898844,
  "data": {
    "data": [
      {
        "id": 1251111922229444400,
        "coin": "BTC",
        "receiver": 1128763679,
        "amount": 0.0072366,
        "status": 6,
        "fromUid": 1128763678,
        "recordType": "out"
      }
    ],
    "total": 1
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/wallets/v1/capital/innerTransfer/records'
    method = "GET"
    paramsMap = {
    "recvWindow": "30000",
    "limit": "1000",
    "coin": "BTC",
    "startTime": "1701519898118",
    "endTime": "1702383898118"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Asset overview

**GET** `/openApi/account/v1/allAccountBalance`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| accountType | string | No | Account type, if left blank, all assets of the account will be checked by default. spot: spot (fund account), stdFutures: standard futures account, coinMPerp: coin base account, USDTMPerp: U base account, copyTrading: copy trading account, grid: grid account, eran: wealth account, c2c: c2c account. |
| timestamp | int64 | Yes | Request valid time window value, Unit: milliseconds |
| recvWindow | int64 | No | Timestamp of initiating the request, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| accountType | string | Account type, if left blank, all assets of the account will be checked by default. spot: spot (fund account), stdFutures: standard futures account, coinMPerp: coin base account, USDTMPerp: U base account, copyTrading: copy trading account, grid: grid account, eran: wealth account, c2c: c2c account. |
| usdtBalance | string | Equivalent to USDT amount |

**Request Example**

```json
{
  "accountType": "sopt",
  "recvWindow": "6000"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1719494258281,
  "data": {
    "result": [
      {
        "accountType": "sopt",
        "usdtBalance": "100"
      }
    ],
    "pageId": 1,
    "total": 1
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/account/v1/allAccountBalance'
    method = "GET"
    paramsMap = {
    "accountType": "sopt",
    "recvWindow": "6000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Wallet deposits and withdrawals

#### Deposit records

**GET** `/openApi/api/v3/capital/deposit/hisrec`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| coin | string | No | coin name |
| status | int64 | No | Status (0-In progress 6-Chain uploaded 1-Completed) |
| startTime | LONG | No | Starting time1658748648396 |
| endTime | LONG | No | End Time 1658748648396 |
| offset | int64 | No | offset default0 |
| limit | int64 | No | Page size default 1000 cannot exceed 1000 |
| txId | LONG | No | transaction id |
| recvWindow | LONG | No | Execution window time, cannot be greater than 60000 |
| timestamp | LONG | Yes | current timestamp 1658748648396 |

**Response Body**

| filed | data type | description |
|---|---|---|
| amount | DECIMAL | Recharge amount |
| coin | string | coin name |
| network | string | recharge network |
| status | int64 | Status (0-In progress 6-Chain uploaded 1-Completed) |
| address | string | recharge address |
| addressTag | string | Remark |
| txId | LONG | transaction id |
| insertTime | LONG | transaction hour |
| transferType | LONG | Transaction Type 0 = Recharge |
| unlockConfirm | LONG | confirm times for unlocking |
| confirmTimes | LONG | Network confirmation times |
| sourceAddress | String | Source address |

**Request Example**

```json
{
  "endTime": "1702622588000",
  "recvWindow": "5000",
  "startTime": "1700894588000"
}
```

**Response Example**

```json
[
  {
    "amount": "49999.00000000000000000000",
    "coin": "USDTTRC20",
    "network": "TRC20",
    "status": 1,
    "address": "TP******B4v",
    "addressTag": "",
    "txId": "60*****1d",
    "insertTime": 1701557778000,
    "unlockConfirm": "2/2",
    "confirmTimes": "2/2"
  }
]
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/api/v3/capital/deposit/hisrec'
    method = "GET"
    paramsMap = {
    "endTime": "1702622588000",
    "recvWindow": "5000",
    "startTime": "1700894588000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Withdraw records

**GET** `/openApi/api/v3/capital/withdraw/history`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| id | string | No | Unique id of the withdrawal record returned by the platform |
| coin | string | No | coin name |
| withdrawOrderId | string | No | Custom ID, if there is none, this field will not be returned,When both the platform ID and withdraw order ID are passed as parameters, the query will be based on the platform ID |
| status | int64 | No | 4-Under Review 5-Failed 6-Completed |
| startTime | LONG | No | Starting time1658748648396 |
| endTime | LONG | No | End Time 1658748648396 |
| offset | int64 | No | offset default0 |
| limit | int64 | No | Page size default 1000 cannot exceed 1000 |
| txId | String | No | Withdrawal transaction id |
| recvWindow | LONG | No | Execution window time, cannot be greater than 60000 |
| timestamp | LONG | Yes | current timestamp e.g.1658748648396 |

**Response Body**

| filed | data type | description |
|---|---|---|
| address | string | address |
| amount | DECIMAL | Withdrawal amount |
| applyTime | Date | withdraw time |
| coin | string | coin name |
| id | string | The id of the withdrawal |
| withdrawOrderId | string | Custom ID, if there is none, this field will not be returned,When both the platform ID and withdraw order ID are passed as parameters, the query will be based on the platform ID |
| network | string | Withdrawal network |
| status | int64 | 4-Under Review 5-Failed 6-Completed |
| transactionFee | string | handling fee |
| confirmNo | int64 | Withdrawal confirmation times |
| info | string | Reason for withdrawal failure |
| txId | String | Withdrawal transaction id |
| sourceAddress | String | Source address |
| transferType | int64 | Transfer type: 1 Withdrawal, 2 Internal transfer |
| addressTag | string | Some currencies like XRP/XMR allow filling in secondary address tags |

**Request Example**

```json
{
  "coin": "USDT",
  "endTime": "1702536564000",
  "recvWindow": "60",
  "startTime": "1702450164000"
}
```

**Response Example**

```json
[
  {
    "address": "TR****zc",
    "amount": "3500.00000000000000000000",
    "applyTime": "2023-12-14T04:05:02.000+08:00",
    "coin": "USDTTRC20",
    "id": "125*****98",
    "network": "TRC20",
    "transferType": 1,
    "transactionFee": "1.00000000000000000000",
    "confirmNo": 2,
    "info": "",
    "txId": "b9***********b67"
  }
]
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/api/v3/capital/withdraw/history'
    method = "GET"
    paramsMap = {
    "coin": "USDT",
    "endTime": "1702536564000",
    "recvWindow": "60",
    "startTime": "1702450164000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query currency deposit and withdrawal data

**GET** `/openApi/wallets/v1/capital/config/getall`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| coin | string | No | Coin identification |
| displayName | string | No | The platform displays the currency pair name for display only. Unlike coins, coins need to be used for withdrawal and recharge. |
| timestamp | int64 | Yes | Timestamp of initiating the request, Unit: milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| coin | string | Coin identification |
| displayName | string | The platform displays the currency pair name for display only. Unlike coins, coins need to be used for withdrawal and recharge. |
| name | string | Coin name |
| networkList | Network | Network information |

**Request Example**

```json
{}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1702623271477,
  "data": [
    {
      "coin": "BTC",
      "name": "BTC",
      "networkList": [
        {
          "name": "BTC",
          "network": "BTC",
          "isDefault": true,
          "minConfirm": 2,
          "withdrawEnable": true,
          "depositEnable": true,
          "withdrawFee": "0.0006",
          "withdrawMax": "1.17522",
          "withdrawMin": "0.0005",
          "depositMin": "0.0002"
        },
        {
          "name": "BTC",
          "network": "BEP20",
          "isDefault": false,
          "minConfirm": 15,
          "withdrawEnable": true,
          "depositEnable": true,
          "withdrawFee": "0.0000066",
          "withdrawMax": "1.17522",
          "withdrawMin": "0.0000066",
          "depositMin": "0.0002"
        }
      ]
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/wallets/v1/capital/config/getall'
    method = "GET"
    paramsMap = {}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Withdraw

**POST** `/openApi/wallets/v1/capital/withdraw/apply`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| coin | string | Yes | Coin name |
| network | string | No | Network name, use default network if not transmitted |
| address | string | Yes | Withdrawal address |
| addressTag | string | No | Tag or memo, some currencies support tag or memo |
| amount | float64 | Yes | Withdrawal amount |
| walletType | int64 | Yes | Account type, 1 Fund Account; 2 Standard Futures Account; 3 Perpetual Futures Account; 4 Spot Account. When the funding account balance is insufficient, the system will automatically replenish funds from the spot account. |
| withdrawOrderId | string | No | Customer-defined withdrawal ID, a combination of numbers and letters, with a length of less than 100 characters |
| vaspEntityId | string | No | Payment platform information, only KYC=KOR (Korean individual users) must pass this field. List values Bithumb, Coinone, Hexlant, Korbit, Upbit, Others, and select Others if there are no corresponding options |
| recipientLastName | string | No | The recipient's surname is in English, and only KYC=KOR (Korean individual users) must pass this field. No need to fill in when vaspAntityId=Others |
| recipientFirstName | string | No | The recipient's name in English, only KYC=KOR (Korean individual users) must pass this field. No need to fill in when vaspAntityId=Others. |
| dateOfbirth | string | No | The payee's date of birth (example 1999-09-09) must be passed as this field only for KYC=KOR (Korean individual users). No need to fill in when vaspAntityId=Others. |
| timestamp | int64 | Yes | Timestamp of initiating the request, Unit: milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| id | string | The platform returns the unique ID of the internal transfer record. |
| withdrawOrderId | string | Customer-defined withdrawal ID, a combination of numbers and letters, with a length of less than 100 characters |

**Request Example**

```json
{
  "address": "0x8****11",
  "addressTag": "None",
  "amount": "4998.0",
  "coin": "USDT",
  "network": "BEP20",
  "walletType": "1"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1702619168218,
  "data": {
    "id": "125*****4"
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/wallets/v1/capital/withdraw/apply'
    method = "POST"
    paramsMap = {
    "address": "0x8****11",
    "addressTag": "None",
    "amount": "4998.0",
    "coin": "USDT",
    "network": "BEP20",
    "walletType": "1"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Main Account Deposit Address

**GET** `/openApi/wallets/v1/capital/deposit/address`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| coin | string | Yes | Name of the coin for transfer |
| offset | int64 | No | Starting record number, default is 0 |
| limit | int64 | No | Page size, default is 100, maximum is 1000 |
| timestamp | int64 | Yes | Timestamp of the request in milliseconds |
| recvWindow | int64 | No | Request window validity, in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| data | object | List of deposit addresses |
| total | int64 | Total number of addresses |
| coin | string | Name of the coin |
| network | string | Name of the network |
| address | string | Deposit address |
| addressWithPrefix | string | Deposit address with prefix |
| tag | string | Address tag |
| status | int64 | 0 for activated, 1 for applied, 2 for not applied |
| walletType | int64 | Account type, 1 Fund Account; 2 Standard Futures Account; 3 Perpetual Futures Account; 4 Spot Account |

**Request Example**

```json
{
  "coin": "USDT",
  "limit": "1000",
  "offset": "0",
  "recvWindow": "0"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1702623918163,
  "data": {
    "data": [
      {
        "coinId": 760,
        "coin": "USDT",
        "network": "ERC20",
        "address": "40e*****95",
        "tag": ""
      },
      {
        "coinId": 780,
        "coin": "USDT",
        "network": "TRC20",
        "address": "40e*****95",
        "tag": ""
      },
      {
        "coinId": 799,
        "coin": "USDT",
        "network": "BEP20",
        "address": "40e*****95",
        "tag": ""
      },
      {
        "coinId": 857,
        "coin": "USDT",
        "network": "SOL",
        "address": "40e*****95",
        "tag": ""
      },
      {
        "coinId": 1192,
        "coin": "USDT",
        "network": "POLYGON",
        "address": "40e*****95",
        "tag": ""
      },
      {
        "coinId": 1367,
        "coin": "USDT",
        "network": "ARBITRUM",
        "address": "40e*****95",
        "tag": ""
      },
      {
        "coinId": 1371,
        "coin": "USDT",
        "network": "OPTIMISM",
        "address": "40e*****95",
        "tag": ""
      }
    ],
    "total": 7
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/wallets/v1/capital/deposit/address'
    method = "GET"
    paramsMap = {
    "coin": "USDT",
    "limit": "1000",
    "offset": "0",
    "recvWindow": "0"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Deposit risk control records

**GET** `/openApi/wallets/v1/capital/deposit/riskRecords`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| filed | data type | description |  |

**Request Example**

```json
{}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1706839654997,
  "data": [
    {
      "uid": "",
      "coin": "",
      "amount": "",
      "sourceAddress": "",
      "address": "",
      "insetTime": ""
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/wallets/v1/capital/deposit/riskRecords'
    method = "GET"
    paramsMap = {}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Trades Endpoints

#### Place order

**POST** `/openApi/swap/v2/trade/order`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| type | string | Yes | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order / TRAILING_TP_SL: Trailing TakeProfit or StopLoss |
| side | string | Yes | buying and selling direction SELL, BUY |
| positionSide | string | No | Position direction, required for single position as BOTH, for both long and short positions only LONG or SHORT can be chosen, defaults to LONG if empty |
| reduceOnly | string | No | true, false; Default value is false for single position mode; This parameter is not accepted for both long and short positions mode |
| price | float64 | No | Price, represents the trailing stop distance in TRAILING_STOP_MARKET and TRAILING_TP_SL |
| quantity | float64 | No | Original quantity, only support units by COIN ,Ordering with quantity U is not currently supported. |
| quoteOrderQty | float64 | No | Quote order quantity, e.g., 100USDT,if quantity and quoteOrderQty are input at the same time, quantity will be used first, and quoteOrderQty will be discarded |
| stopPrice | float64 | No | Trigger price, only required for STOP_MARKET, TAKE_PROFIT_MARKET, STOP, TAKE_PROFIT, TRIGGER_LIMIT, TRIGGER_MARKET |
| priceRate | float64 | No | For type: TRAILING_STOP_MARKET or TRAILING_TP_SL; Maximum: 1 |
| workingType | string | No | The stopPrice trigger price type can be MARK_PRICE, CONTRACT_PRICE, or INDEX_PRICE, with the default set to MARK_PRICE. When the order type is STOP or STOP_MARKET and stopGuaranteed = true, the workingType can only be set to CONTRACT_PRICE. |
| timestamp | int64 | Yes | Support setting take profit while placing an order. Only supports type: TAKE_PROFIT_MARKET/TAKE_PROFIT |
| stopLoss | string | No | StopPrice trigger price types: MARK_PRICE, CONTRACT_PRICE, INDEX_PRICE, default MARK_PRICE. When the type is STOP or STOP_MARKET, and stopGuaranteed is true, the workingType must only be CONTRACT_PRICE. |
| takeProfit | string | No | request timestamp, unit: millisecond |
| clientOrderId | string | No | Customized order ID for users, with a limit of characters from 1 to 40. The system will convert this field to lowercase. Different orders cannot use the same clientOrderId, clientOrderId only supports LIMIT/MARKET order type |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |
| timeInForce | string | No | Time in Force, currently supports PostOnly, GTC, IOC, and FOK |
| closePosition | string | No | true, false; all position squaring after triggering, only support STOP_MARKET and TAKE_PROFIT_MARKET; not used with quantity; comes with only position squaring effect, not used with reduceOnly |
| activationPrice | float64 | No | Used with TRAILING_STOP_MARKET or TRAILING_TP_SL orders, default as the latest price(supporting different workingType) |
| stopGuaranteed | string | No | true: Enables the guaranteed stop-loss and take-profit feature; false: Disables the feature; cutfee: Enable the guaranteed stop loss function and enable the VIP guaranteed stop loss fee reduction function. When stopGuaranteed is true or cutfee, the quantity field does not take effect. The guaranteed stop-loss feature is not enabled by default. Supported order types include: STOP_MARKET: Market stop-loss order / TAKE_PROFIT_MARKET: Market take-profit order / STOP: Limit stop-loss order / TAKE_PROFIT: Limit take-profit order / TRIGGER_LIMIT: Stop-limit order with trigger / TRIGGER_MARKET: Market order with trigger for stop-loss. |
| positionId | int64 | No | In the Separate Isolated mode, closing a position must be transmitted |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | trading pair, for example: BTC-USDT |
| side | string | buying and selling direction |
| type | string | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order / TRAILING_TP_SL: Trailing TakeProfit or StopLoss |
| positionSide | string | Position direction, required for single position as BOTH, for both long and short positions only LONG or SHORT can be chosen, defaults to LONG if empty |
| reduceOnly | string | true, false; Default value is false for single position mode; This parameter is not accepted for both long and short positions mode |
| orderID | string | Order ID |
| workingType | string | StopPrice trigger price types: MARK_PRICE, CONTRACT_PRICE, INDEX_PRICE, default MARK_PRICE. When the type is STOP or STOP_MARKET, and stopGuaranteed is true, the workingType must only be CONTRACT_PRICE. |
| clientOrderId | string | Customized order ID for users. The system will convert this field to lowercase. |
| stopGuaranteed | string | true: Enables the guaranteed stop-loss and take-profit feature; false: Disables the feature; cutfee: Enable the guaranteed stop loss function and enable the VIP guaranteed stop loss fee reduction function. The VIP fee reduction only takes effect when placing a stop loss order.. The guaranteed stop-loss feature is not enabled by default. Supported order types include: STOP_MARKET: Market stop-loss order / TAKE_PROFIT_MARKET: Market take-profit order / STOP: Limit stop-loss order / TAKE_PROFIT: Limit take-profit order / TRIGGER_LIMIT: Stop-limit order with trigger / TRIGGER_MARKET: Market order with trigger for stop-loss. |
| status | string | Order status |
| avgPrice | string | Average filled price, present when type=MARKET |
| executedQty | string | Transaction quantity, coins |

**Request Example**

```json
[
  {
    "title": "MARKET",
    "desc": "Place an order at market price and set a take profit",
    "payload": {
      "symbol": "BTC-USDT",
      "side": "BUY",
      "positionSide": "LONG",
      "type": "MARKET",
      "quantity": 5,
      "takeProfit": "{\"type\": \"TAKE_PROFIT_MARKET\", \"stopPrice\": 31968.0,\"price\": 31968.0,\"workingType\":\"MARK_PRICE\"}"
    }
  },
  {
    "title": "STOP_MARKET",
    "desc": "Market stop loss order",
    "payload": {
      "type": "STOP_MARKET",
      "stopPrice": 50000,
      "symbol": "BTC-USDT",
      "side": "SELL",
      "quantity": 0.002,
      "positionSide": "LONG",
      "clientOrderID": "",
      "recvWindow": 1000,
      "timeInForce": "GTC",
      "workingType": "",
      "timestamp": 1726223068783
    }
  },
  {
    "title": "TAKE_PROFIT_MARKET",
    "desc": "Market price take profit order",
    "payload": {
      "type": "TAKE_PROFIT_MARKET",
      "stopPrice": 70000,
      "symbol": "BTC-USDT",
      "side": "SELL",
      "quantity": 0.002,
      "positionSide": "LONG",
      "clientOrderID": "",
      "recvWindow": 1000,
      "timeInForce": "GTC",
      "workingType": "",
      "timestamp": 1726223068783
    }
  },
  {
    "title": "STOP",
    "desc": "Stop limit order",
    "payload": {
      "type": "STOP",
      "price": 50000,
      "stopPrice": 50000,
      "priceRate": 0,
      "symbol": "BTC-USDT",
      "side": "SELL",
      "quantity": 0.002,
      "positionSide": "LONG",
      "clientOrderID": "",
      "recvWindow": 1000,
      "timeInForce": "GTC",
      "workingType": "",
      "timestamp": 1726223068783
    }
  },
  {
    "title": "TAKE_PROFIT",
    "desc": "Limit price and take profit order",
    "payload": {
      "type": "TAKE_PROFIT",
      "price": 70000,
      "stopPrice": 70000,
      "priceRate": 0,
      "symbol": "BTC-USDT",
      "side": "SELL",
      "quantity": 0.002,
      "positionSide": "LONG",
      "clientOrderID": "",
      "recvWindow": 1000,
      "timeInForce": "GTC",
      "workingType": "",
      "timestamp": 1726223068783
    }
  },
  {
    "title": "TRIGGER_LIMIT",
    "desc": "Limit order with trigger",
    "payload": {
      "type": "TRIGGER_LIMIT",
      "price": 70000,
      "stopPrice": 70000,
      "priceRate": 0,
      "symbol": "BTC-USDT",
      "side": "BUY",
      "quantity": 0.002,
      "positionSide": "LONG",
      "clientOrderID": "",
      "takeProfit": "",
      "recvWindow": 1000,
      "stopLoss": "",
      "timeInForce": "GTC",
      "workingType": "",
      "timestamp": 1726223068783
    }
  },
  {
    "title": "TRIGGER_MARKET",
    "desc": "Market order with trigger",
    "payload": {
      "type": "TRIGGER_MARKET",
      "stopPrice": 70000,
      "symbol": "BTC-USDT",
      "side": "BUY",
      "quantity": 0.002,
      "positionSide": "LONG",
      "clientOrderID": "",
      "takeProfit": "",
      "recvWindow": 1000,
      "stopLoss": "",
      "timeInForce": "GTC",
      "workingType": "",
      "timestamp": 1726223068783
    }
  },
  {
    "title": "TRAILING_STOP_MARKET",
    "desc": "Trailing Stop Market Order",
    "payload": {
      "type": "TRAILING_STOP_MARKET",
      "price": 0,
      "stopPrice": 0,
      "priceRate": 0.1,
      "symbol": "BTC-USDT",
      "side": "BUY",
      "quantity": 0.002,
      "positionSide": "LONG",
      "clientOrderID": "",
      "recvWindow": 1000,
      "timeInForce": "GTC",
      "workingType": "",
      "timestamp": 1726223068783
    }
  },
  {
    "title": "TRAILING_TP_SL",
    "desc": "Trailing TakeProfit or StopLoss",
    "payload": {
      "type": "TRAILING_TP_SL",
      "price": 0,
      "stopPrice": 0,
      "priceRate": 0.1,
      "symbol": "BTC-USDT",
      "side": "SELL",
      "quantity": 0.002,
      "positionSide": "LONG",
      "clientOrderID": "",
      "recvWindow": 1000,
      "timeInForce": "GTC",
      "workingType": "",
      "timestamp": 1726231037325
    }
  },
  {
    "title": "POSITION_STOP_MARKET",
    "desc": "Market price position stop loss order",
    "payload": {
      "type": "STOP_MARKET",
      "closePosition": true,
      "stopPrice": 50000,
      "symbol": "BTC-USDT",
      "side": "SELL",
      "quantity": 0.002,
      "positionSide": "LONG",
      "clientOrderID": "",
      "recvWindow": 1000,
      "timeInForce": "GTC",
      "workingType": "",
      "timestamp": 1726223068783
    }
  },
  {
    "title": "POSITION_TAKE_PROFIT_MARKET",
    "desc": "Market price position take profit order",
    "payload": {
      "type": "TAKE_PROFIT_MARKET",
      "closePosition": true,
      "stopPrice": 70000,
      "symbol": "BTC-USDT",
      "side": "SELL",
      "quantity": 0.002,
      "positionSide": "LONG",
      "clientOrderID": "",
      "recvWindow": 1000,
      "timeInForce": "GTC",
      "workingType": "",
      "timestamp": 1726223068783
    }
  }
]
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "order": {
      "symbol": "BTC-USDT",
      "orderId": 1735950529123455000,
      "side": "BUY",
      "positionSide": "LONG",
      "type": "MARKET",
      "clientOrderId": "",
      "workingType": "MARK_PRICE"
    }
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 101204 | Insufficient margin |
| 109400 | timestamp is invalid |
| 101205 | No position to close |
| 109429 | Too many repeated errors |
| 101253 | Insufficient margin |
| 101400 | clientOrderID unique check failed |
| 110424 | Order size exceeds available amount |
| 109425 | Trading pair does not exist |
| 101212 | Available amount is insufficient |
| 101485 | Order size below minimum |
| 100004 | Permission denied |
| 101209 | Maximum position value reached |
| 101222 | Leverage risk too high |
| 100413 | Incorrect API key |
| 109420 | Position not exist |
| 101484 | Advanced verification required |
| 110411 | Invalid Stop Loss price |
| 100410 | Rate limited |
| 100001 | Signature verification failed |
| 110413 | Invalid Take Profit price |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/order'
    method = "POST"
    paramsMap = {
    "symbol": "BTC-USDT",
    "side": "BUY",
    "positionSide": "LONG",
    "type": "MARKET",
    "quantity": 5,
    "takeProfit": "{\"type\": \"TAKE_PROFIT_MARKET\", \"stopPrice\": 31968.0,\"price\": 31968.0,\"workingType\":\"MARK_PRICE\"}"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Place multiple orders

**POST** `/openApi/swap/v2/trade/batchOrders`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| batchOrders | LIST<Order> | Yes | Order list, supporting up to 5 orders, with Order objects referencing transactions to place orders |
| timestamp | int64 | Yes | request timestamp, unit: millisecond |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | trading pair, for example: BTC-USDT |
| side | string | buying and selling direction |
| type | string | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order / TRAILING_TP_SL: Trailing TakeProfit or StopLoss |
| positionSide | string | Position direction, required for single position as BOTH, for both long and short positions only LONG or SHORT can be chosen, defaults to LONG if empty |
| reduceOnly | string | true, false; Default value is false for single position mode; This parameter is not accepted for both long and short positions mode |
| orderID | string | Order ID |
| workingType | string | Customized order ID for users. The system will convert this field to lowercase. |
| clientOrderId | string | true: Enables the guaranteed stop-loss and take-profit feature; false: Disables the feature. The guaranteed stop-loss feature is not enabled by default. Supported order types include: STOP_MARKET: Market stop-loss order / TAKE_PROFIT_MARKET: Market take-profit order / STOP: Limit stop-loss order / TAKE_PROFIT: Limit take-profit order / TRIGGER_LIMIT: Stop-limit order with trigger / TRIGGER_MARKET: Market order with trigger for stop-loss. |
| stopGuaranteed | string | Order status |
| status | string | Average filled price, present when type=MARKET |
| avgPrice | string | Transaction quantity, coins |

**Request Example**

```json
{
  "batchOrders": "[{\"symbol\": \"ETH-USDT\",\"type\": \"MARKET\",\"side\": \"BUY\",\"positionSide\": \"LONG\",\"quantity\": 1},{\"symbol\": \"BTC-USDT\",\"type\": \"MARKET\",\"side\": \"BUY\",\"positionSide\": \"LONG\",\"quantity\": 0.001}]"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "orders": [
      {
        "symbol": "ID-USDT",
        "orderId": 1736010300483712300,
        "side": "SELL",
        "positionSide": "LONG",
        "type": "MARKET",
        "clientOrderId": "",
        "workingType": ""
      }
    ]
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109403 | Risk forbidden |
| 112414 | Total position amount reached platform limit |
| 101400 | Order amount below minimum |
| 109500 | Invalid symbol format |
| 100500 | System busy |
| 110420 | Invalid TP/SL or activation price |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/batchOrders'
    method = "POST"
    paramsMap = {
    "batchOrders": "[{\"symbol\": \"ETH-USDT\",\"type\": \"MARKET\",\"side\": \"BUY\",\"positionSide\": \"LONG\",\"quantity\": 1},{\"symbol\": \"BTC-USDT\",\"type\": \"MARKET\",\"side\": \"BUY\",\"positionSide\": \"LONG\",\"quantity\": 0.001}]"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Cancel Order

**DELETE** `/openApi/swap/v2/trade/order`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| orderId | int64 | No | Order ID |
| clientOrderId | string | No | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| symbol | string | Yes | Customized order ID for users, with a limit of characters from 1 to 40. The system will convert this field to lowercase. Different orders cannot use the same clientOrderId |
| timestamp | int64 | Yes | request timestamp, unit: millisecond |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| time | int64 | order time, unit: millisecond |
| symbol | string | trading pair, for example: BTC-USDT |
| side | string | buying and selling direction |
| type | string | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order |
| positionSide | string | position side |
| cumQuote | string | transaction amount |
| status | string | order status |
| stopPrice | string | Trigger price |
| price | string | Price |
| origQty | string | original order quantity |
| avgPrice | string | average transaction price |
| executedQty | string | volume |
| orderId | int64 | Order ID |
| profit | string | profit and loss |
| commission | string | Fee |
| updateTime | int64 | update time, unit: millisecond |
| clientOrderId | string | Customized order ID for users. The system will convert this field to lowercase. |

**Request Example**

```json
{
  "orderId": "1736011869418901234",
  "symbol": "RNDR-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "order": {
      "symbol": "RNDR-USDT",
      "orderId": 1736011869418901200,
      "side": "BUY",
      "positionSide": "LONG",
      "type": "LIMIT",
      "origQty": "3",
      "price": "4.5081",
      "executedQty": "0",
      "avgPrice": "0.0000",
      "cumQuote": "0",
      "stopPrice": "",
      "profit": "0.0000",
      "commission": "0.000000",
      "status": "CANCELLED",
      "time": 1702732457867,
      "updateTime": 1702732457888,
      "clientOrderId": "lo******7",
      "leverage": "",
      "takeProfit": {
        "type": "",
        "quantity": 0,
        "stopPrice": 0,
        "price": 0,
        "workingType": ""
      },
      "stopLoss": {
        "type": "",
        "quantity": 0,
        "stopPrice": 0,
        "price": 0,
        "workingType": ""
      },
      "advanceAttr": 0,
      "positionID": 0,
      "takeProfitEntrustPrice": 0,
      "stopLossEntrustPrice": 0,
      "orderType": "",
      "workingType": ""
    }
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 109201 | The same order number is only allowed to be submitted once within 1 second. |
| 80018 | order is already filled, The order doesn't exist |
| 80018 | order is already filled, The order doesn't exist |
| 80001 | service has some errors, The order doesn't exist |
| 109414 | order not exist |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/order'
    method = "DELETE"
    paramsMap = {
    "orderId": "1736011869418901234",
    "symbol": "RNDR-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Cancel multiple orders

**DELETE** `/openApi/swap/v2/trade/batchOrders`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| orderIdList | LIST<int64> | No | system order number, up to 10 orders [1234567,2345678] |
| clientOrderIdList | LIST<string> | No | Customized order ID for users, up to 10 orders ["abc1234567","abc2345678"]. The system will convert this field to lowercase. |
| symbol | string | Yes | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| timestamp | int64 | Yes | request timestamp, unit: millisecond |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int64 | error code, 0 means successfully response, others means response failure |
| msg | string | Error Details Description |
| success | LIST<Order> | list of successfully canceled orders |
| failed | 結构數組 | list of failed orders |
| orderId | int64 | Order ID |
| errorCode | int64 | error code, 0 means successfully response, others means response failure |
| errorMessage | string | Error Details Description |

**Request Example**

```json
{
  "orderIdList": "[1735924831603391122, 1735924833239172233]",
  "symbol": "BTC-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "success": [
      {
        "symbol": "BTC-USDT",
        "orderId": 1735924831603391200,
        "side": "BUY",
        "positionSide": "LONG",
        "type": "LIMIT",
        "origQty": "0.0032",
        "price": "41682.9",
        "executedQty": "0.0000",
        "avgPrice": "0.0",
        "cumQuote": "0",
        "stopPrice": "",
        "profit": "0.0000",
        "commission": "0.000000",
        "status": "CANCELLED",
        "time": 1702711706435,
        "updateTime": 1702711706453,
        "clientOrderId": "",
        "leverage": "",
        "takeProfit": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": ""
        },
        "stopLoss": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": ""
        },
        "advanceAttr": 0,
        "positionID": 0,
        "takeProfitEntrustPrice": 0,
        "stopLossEntrustPrice": 0,
        "orderType": "",
        "workingType": ""
      },
      {
        "symbol": "BTC-USDT",
        "orderId": 1735924833239172400,
        "side": "BUY",
        "positionSide": "LONG",
        "type": "LIMIT",
        "origQty": "0.0033",
        "price": "41182.9",
        "executedQty": "0.0000",
        "avgPrice": "0.0",
        "cumQuote": "0",
        "stopPrice": "",
        "profit": "0.0000",
        "commission": "0.000000",
        "status": "CANCELLED",
        "time": 1702711706825,
        "updateTime": 1702711706838,
        "clientOrderId": "",
        "leverage": "",
        "takeProfit": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": ""
        },
        "stopLoss": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": ""
        },
        "advanceAttr": 0,
        "positionID": 0,
        "takeProfitEntrustPrice": 0,
        "stopLossEntrustPrice": 0,
        "orderType": "",
        "workingType": ""
      }
    ],
    "failed": null
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 80014 | orderIdList & clientOrderIDList are both empty; |
| 109201 | The same order number is only allowed to be submitted once within 1 second. |
| 109201 | The same order number is only allowed to be submitted once within 1 second. |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/batchOrders'
    method = "DELETE"
    paramsMap = {
    "orderIdList": "[1735924831603391122, 1735924833239172233]",
    "symbol": "BTC-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Cancel all Open Orders on a Symbol

**POST** `/openApi/spot/v1/trade/cancelOpenOrders`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | Trading pair, e.g., BTC-USDT,If not filled out, cancel all orders. |
| recvWindow | float64 | No | Request valid time window value, Unit: milliseconds |
| timestamp | int64 | Yes | Timestamp of initiating the request, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | Trading pair |
| orderId | int64 | Order ID |
| price | string | Price |
| origQty | string | Original quantity |
| executedQty | string | Executed quantity |
| cummulativeQuoteQty | string | Cumulative quote asset transacted quantity |
| status | string | Order status: NEW, PENDING, PARTIALLY_FILLED, FILLED, CANCELED, FAILED |
| type | string | MARKET/LIMIT/TAKE_STOP_LIMIT/TAKE_STOP_MARKET/TRIGGER_LIMIT/TRIGGER_MARKET |
| side | string | BUY/SELL |
| clientOrderID | string | Customized order ID for users |
| stopPrice | string | trigger price |

**Request Example**

```json
{
  "symbol": "GM-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "debugMsg": "",
  "data": {
    "orders": [
      {
        "symbol": "GM-USDT",
        "orderId": 1735964997957275600,
        "transactTime": 1702721242701,
        "price": "0.00000398",
        "stopPrice": "0.00000398",
        "origQty": "8061558",
        "executedQty": "0",
        "cummulativeQuoteQty": "0",
        "status": "CANCELED",
        "type": "LIMIT",
        "side": "SELL",
        "clientOrderID": "2most51702721242645506402"
      },
      {
        "symbol": "GM-USDT",
        "orderId": 1735965127519326200,
        "transactTime": 1702721249787,
        "price": "0.00000398",
        "stopPrice": "0.00000398",
        "origQty": "5806281",
        "executedQty": "0",
        "cummulativeQuoteQty": "0",
        "status": "CANCELED",
        "type": "LIMIT",
        "side": "SELL",
        "clientOrderID": "2most51702721249647382871"
      }
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/spot/v1/trade/cancelOpenOrders'
    method = "POST"
    paramsMap = {
    "symbol": "GM-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Cancel an Existing Order and Send a New Order

**POST** `/openApi/spot/v1/trade/order/cancelReplace`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | The trading pair, for example: BTC-USDT, please use uppercase letters |
| cancelOrderId | int64 | No | The ID of the order to be canceled |
| cancelClientOrderID | string | No | The user-defined ID of the order to be canceled, character length limit: 1-40, different orders cannot use the same clientOrderID, only supports a query range of 2 hours |
| cancelRestrictions | string | No | Cancel orders with specified status: NEW: New order, PENDING: Pending order, PARTIALLY_FILLED: Partially filled |
| CancelReplaceMode | string | Yes | STOP_ON_FAILURE: If the cancel order fails, it will not continue to place a new order. ALLOW_FAILURE: Regardless of whether the cancel order succeeds or fails, it will continue to place a new order. |
| side | string | Yes | The type of transaction, BUY: Buy, SELL: Sell |
| type | string | Yes | MARKET/LIMIT/TAKE_STOP_LIMIT/TAKE_STOP_MARKET/TRIGGER_LIMIT/TRIGGER_MARKET |
| stopPrice | string | Yes | Trigger price used for TAKE_STOP_LIMIT, TAKE_STOP_MARKET, TRIGGER_LIMIT, TRIGGER_MARKET order types. |
| quantity | float64 | No | Order quantity, e.g. 0.1BTC |
| quoteOrderQty | float64 | No | Order amount, e.g. 100USDT |
| price | float64 | No | Order price, e.g. 10000USDT |
| newClientOrderId | string | No | Custom order ID consisting of letters, numbers, and _. Character length should be between 1-40. Different orders cannot use the same newClientOrderId. |
| recvWindow | float64 | No | Request valid time window in milliseconds. |
| timestamp | int64 | Yes | Request timestamp in milliseconds. |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | Trading symbol |
| orderId | int64 | Order ID |
| price | string | Order price |
| origQty | string | Order quantity |
| executedQty | string | Executed quantity |
| cummulativeQuoteQty | string | Cumulative quote quantity |
| status | string | Order status: NEW (new order), PENDING (pending), PARTIALLY_FILLED (partially filled), FILLED (filled), CANCELED (cancelled), FAILED (failed) |
| type | string | Order type: MARKET/LIMIT/TAKE_STOP_LIMIT/TAKE_STOP_MARKET/TRIGGER_LIMIT/TRIGGER_MARKET |
| side | string | Transaction type: BUY (buy), SELL (sell) |
| clientOrderID | string | User-defined order ID |
| stopPrice | string | Trigger price |
| cancelRestrictions | string | Cancel orders in specific states: NEW (new order), PENDING (pending), PARTIALLY_FILLED (partially filled) |
| transactTime | int64 | Transaction timestamp |

**Request Example**

```json
{
  "symbol": "BTC-USDT",
  "cancelOrderId": "17543893539094511234",
  "cancelReplaceMode": "ALLOW_FAILURE",
  "side": "BUY",
  "type": "LIMIT",
  "price": 40000,
  "quantity": 1
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "debugMsg": "",
  "data": {
    "cancelResult": {
      "code": 100400,
      "msg": " order not exist",
      "result": false
    },
    "openResult": {
      "code": 0,
      "msg": "",
      "result": true
    },
    "orderOpenResponse": {
      "symbol": "BTC-USDT",
      "orderId": 1754389353909452800,
      "transactTime": 1707113991607,
      "price": "40000",
      "stopPrice": "0",
      "origQty": "1",
      "executedQty": "0",
      "cummulativeQuoteQty": "0",
      "status": "PENDING",
      "type": "LIMIT",
      "side": "BUY",
      "clientOrderID": ""
    },
    "orderCancelResponse": {
      "symbol": "",
      "orderId": 0,
      "price": "0",
      "stopPrice": "0",
      "origQty": "0",
      "executedQty": "0",
      "cummulativeQuoteQty": "0",
      "status": "",
      "type": "",
      "side": ""
    }
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/spot/v1/trade/order/cancelReplace'
    method = "POST"
    paramsMap = {
    "symbol": "BTC-USDT",
    "cancelOrderId": "17543893539094511234",
    "cancelReplaceMode": "ALLOW_FAILURE",
    "side": "BUY",
    "type": "LIMIT",
    "price": 40000,
    "quantity": 1
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Order details

**GET** `/openApi/swap/v2/trade/order`

- **Rate Limit**: UID Rate Limit 30/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| orderId | int64 | No | Order ID |
| clientOrderId | string | No | Customized order ID for users, with a limit of characters from 1 to 40. The system will convert this field to lowercase. Different orders cannot use the same clientOrderId |
| timestamp | int64 | Yes | request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| time | int64 | order time, unit: millisecond |
| symbol | string | trading pair, for example: BTC-USDT |
| side | string | buying and selling direction |
| type | string | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order |
| positionSide | string | Position direction, required for single position as BOTH, for both long and short positions only LONG or SHORT can be chosen, defaults to LONG if empty |
| reduceOnly | string | true, false; Default value is false for single position mode; This parameter is not accepted for both long and short positions mode |
| cumQuote | string | transaction amount |
| status | string | order status |
| stopPrice | string | Trigger price |
| price | string | Price |
| origQty | string | original order quantity |
| avgPrice | string | average transaction price |
| executedQty | string | volume |
| orderId | int64 | Order ID |
| profit | string | profit and loss |
| commission | string | Fee |
| updateTime | int64 | update time, unit: millisecond |
| clientOrderId | string | StopPrice trigger price types: MARK_PRICE, CONTRACT_PRICE, INDEX_PRICE, default MARK_PRICE |
| workingType | string | Customized order ID for users. The system will convert this field to lowercase. |
| stopGuaranteed | string | true: Enables the guaranteed stop-loss and take-profit feature; false: Disables the feature. The guaranteed stop-loss feature is not enabled by default. Supported order types include: STOP_MARKET: Market stop-loss order / TAKE_PROFIT_MARKET: Market take-profit order / STOP: Limit stop-loss order / TAKE_PROFIT: Limit take-profit order / TRIGGER_LIMIT: Stop-limit order with trigger / TRIGGER_MARKET: Market order with trigger for stop-loss. |
| triggerOrderId | int64 | trigger order ID associated with this order |
| closePosition | string | Whether to close the entire position |

**Request Example**

```json
{
  "orderId": "1736012449498123456",
  "symbol": "OP-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "order": {
      "symbol": "OP-USDT",
      "orderId": 1736012449498123500,
      "side": "SELL",
      "positionSide": "LONG",
      "type": "LIMIT",
      "origQty": "1.0",
      "price": "2.1710",
      "executedQty": "0.0",
      "avgPrice": "0.0000",
      "cumQuote": "0",
      "stopPrice": "",
      "profit": "0.0000",
      "commission": "0.000000",
      "status": "PENDING",
      "time": 1702732596168,
      "updateTime": 1702732596188,
      "clientOrderId": "l*****e",
      "leverage": "",
      "takeProfit": {
        "type": "",
        "quantity": 0,
        "stopPrice": 0,
        "price": 0,
        "workingType": ""
      },
      "stopLoss": {
        "type": "",
        "quantity": 0,
        "stopPrice": 0,
        "price": 0,
        "workingType": ""
      },
      "advanceAttr": 0,
      "positionID": 0,
      "takeProfitEntrustPrice": 0,
      "stopLossEntrustPrice": 0,
      "orderType": "",
      "workingType": "MARK_PRICE",
      "stopGuaranteed": false,
      "triggerOrderId": 1736012449498123500
    }
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 80016 | order does not exist |
| 109414 | Request failed |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/order'
    method = "GET"
    paramsMap = {
    "orderId": "1736012449498123456",
    "symbol": "OP-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Current Open Orders

**GET** `/openApi/spot/v1/trade/openOrders`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | Trading pair, e.g., BTC-USDT,Query all pending orders when left blank. |
| recvWindow | float64 | No | Request valid time window value, Unit: milliseconds |
| timestamp | int64 | Yes | Timestamp of initiating the request, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| orders | Array | Order list,max length is 2000, refer to the table below for order fields |

**Request Example**

```json
{
  "symbol": "BNB-USDC"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "debugMsg": "",
  "data": {
    "orders": [
      {
        "symbol": "BNB-USDC",
        "orderId": 1735930294290081300,
        "price": "255.27",
        "StopPrice": "0",
        "origQty": "0.16261",
        "executedQty": "0",
        "cummulativeQuoteQty": "0",
        "status": "PENDING",
        "type": "LIMIT",
        "side": "SELL",
        "time": 1702713008841,
        "updateTime": 1702713008841,
        "origQuoteOrderQty": "0",
        "fee": 0
      }
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/spot/v1/trade/openOrders'
    method = "GET"
    paramsMap = {
    "symbol": "BNB-USDC"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Order history

**GET** `/openApi/swap/v2/trade/allOrders`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT.If no symbol is specified, it will query the historical orders for all trading pairs. |
| currency | string | No | USDC or USDT |
| orderId | int64 | No | Only return subsequent orders, and return the latest order by default |
| startTime | int64 | No | Start time, unit: millisecond |
| endTime | int64 | No | End time, unit: millisecond |
| limit | int64 | Yes | number of result sets to return Default: 500 Maximum: 1000 |
| timestamp | int64 | Yes | request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| time | int64 | order time, unit: millisecond |
| symbol | string | trading pair, for example: BTC-USDT.If a specific pair is not provided, a history of transactions for all pairs will be returned |
| side | string | buying and selling direction |
| type | string | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order |
| positionSide | string | Position direction, required for single position as BOTH, for both long and short positions only LONG or SHORT can be chosen, defaults to LONG if empty |
| reduceOnly | string | true, false; Default value is false for single position mode; This parameter is not accepted for both long and short positions mode |
| cumQuote | string | transaction amount |
| status | string | order status |
| stopPrice | string | Trigger price |
| price | string | Price |
| origQty | string | original order quantity |
| avgPrice | string | average transaction price |
| executedQty | string | volume |
| orderId | int64 | Order ID |
| profit | string | profit and loss |
| commission | string | Fee |
| updateTime | int64 | StopPrice trigger price types: MARK_PRICE, CONTRACT_PRICE, INDEX_PRICE, default MARK_PRICE |
| workingType | string | update time, unit: millisecond |
| stopGuaranteed | string | true: Enables the guaranteed stop-loss and take-profit feature; false: Disables the feature. The guaranteed stop-loss feature is not enabled by default. Supported order types include: STOP_MARKET: Market stop-loss order / TAKE_PROFIT_MARKET: Market take-profit order / STOP: Limit stop-loss order / TAKE_PROFIT: Limit take-profit order / TRIGGER_LIMIT: Stop-limit order with trigger / TRIGGER_MARKET: Market order with trigger for stop-loss. |
| triggerOrderId | int64 | trigger order ID associated with this order |
| isTwap | bool | Whether it is a TWAP order, true: yes, false: no |
| mainOrderId | string | TWAP order number |

**Request Example**

```json
{
  "endTime": "1702731995000",
  "limit": "500",
  "startTime": "1702688795000",
  "symbol": "PYTH-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "orders": [
      {
        "symbol": "PYTH-USDT",
        "orderId": 1736007506620112100,
        "side": "SELL",
        "positionSide": "SHORT",
        "type": "LIMIT",
        "origQty": "33",
        "price": "0.3916",
        "executedQty": "33",
        "avgPrice": "0.3916",
        "cumQuote": "13",
        "stopPrice": "",
        "profit": "0.0000",
        "commission": "-0.002585",
        "status": "FILLED",
        "time": 1702731418000,
        "updateTime": 1702731470000,
        "clientOrderId": "",
        "leverage": "15X",
        "takeProfit": {
          "type": "TAKE_PROFIT",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": ""
        },
        "stopLoss": {
          "type": "STOP",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": ""
        },
        "advanceAttr": 0,
        "positionID": 0,
        "takeProfitEntrustPrice": 0,
        "stopLossEntrustPrice": 0,
        "orderType": "",
        "workingType": "MARK_PRICE",
        "stopGuaranteed": false,
        "triggerOrderId": 1736012449498123500
      }
    ]
  }
}
```

**Error Codes**

| code | error msg |
|---|---|
| 80014 | the query range is more than seven days |

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/allOrders'
    method = "GET"
    paramsMap = {
    "endTime": "1702731995000",
    "limit": "500",
    "startTime": "1702688795000",
    "symbol": "PYTH-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query transaction details

**GET** `/openApi/spot/v1/trade/myTrades`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | Trading pair, e.g. BTC-USDT, please use uppercase letters |
| orderId | long | No | Order ID |
| startTime | long | No | Start timestamp, unit: ms |
| endTime | long | No | End timestamp, unit: ms |
| fromId | long | No | Starting trade ID. By default, the latest trade will be retrieved |
| limit | long | No | Default 500, maximum 1000 |
| recvWindow | float64 | No | Request valid time window, unit: milliseconds |
| timestamp | int64 | Yes | Request timestamp, unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | Trading symbol |
| id | int64 | Trade ID |
| orderId | int64 | Order ID |
| price | string | Price of the trade |
| qty | string | Quantity of the trade |
| quoteQty | string | Quote asset quantity traded |
| commission | float64 | Commission amount |
| commissionAsset | string | Commission asset type |
| time | int64 | Trade time |
| isBuyer | bool | Whether the buyer |
| isMaker | bool | Whether the maker |

**Request Example**

```json
{
  "symbol": "BTC-USDT",
  "orderId": 1745362930595004400,
  "limit": 10
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "debugMsg": "",
  "data": {
    "fills": [
      {
        "symbol": "BTC-USDT",
        "id": 36767057,
        "orderId": 1745362930595004400,
        "price": "46820.155",
        "qty": "0.1430254",
        "quoteQty": "6696.471396937",
        "commission": -0.000046483255,
        "commissionAsset": "BTC",
        "time": 1704961925000,
        "isBuyer": true,
        "isMaker": false
      },
      {
        "symbol": "BTC-USDT",
        "id": 36767058,
        "orderId": 1745362930595004400,
        "price": "46820.155",
        "qty": "0.0003844",
        "quoteQty": "17.997667582000002",
        "commission": -1.2493e-7,
        "commissionAsset": "BTC",
        "time": 1704961925000,
        "isBuyer": true,
        "isMaker": false
      }
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/spot/v1/trade/myTrades'
    method = "GET"
    paramsMap = {
    "symbol": "BTC-USDT",
    "orderId": 1745362930595004400,
    "limit": 10
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Trading Commission Rate

**GET** `/openApi/swap/v2/user/commissionRate`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| timestamp | int64 | Yes | request timestamp, unit: millisecond |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| takerCommissionRate | float64 | taker fee rate |
| makerCommissionRate | float64 | maker fee rate |

**Request Example**

```json
{
  "recvWindow": "5000"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "commission": {
      "takerCommissionRate": 0.0005,
      "makerCommissionRate": 0.0002
    }
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/user/commissionRate'
    method = "GET"
    paramsMap = {
    "recvWindow": "5000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Cancel All After

**POST** `/openApi/swap/v2/trade/cancelAllAfter`

- **Rate Limit**: UID Rate Limit 1/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| type | string | Yes | Request type: ACTIVATE-Activate, CLOSE-Close |
| timeOut | int64 | Yes | Activate countdown time (seconds), range: 10s-120s |

**Response Body**

| filed | data type | description |
|---|---|---|
| triggerTime | int64 | Trigger time for deleting all pending orders |
| status | 狀態 | ACTIVATED (Activation successful)/CLOSED (Closed successfully)/FAILED (Failed) |
| note | string | Explanation |

**Request Example**

```json
{
  "type": "ACTIVATE",
  "timeOut": 10
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "debugMsg": "",
  "data": {
    "triggerTime": 1710389137,
    "status": "ACTIVATED",
    "note": "All your spot pending orders will be closed automatically at 2024-03-14 04:05:37 UTC(+0),before that you can cancel the timer, or extend triggerTime time by this request"
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/cancelAllAfter'
    method = "POST"
    paramsMap = {
    "type": "ACTIVATE",
    "timeOut": 10
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Create an OCO Order

**POST** `/openApi/spot/v1/oco/order`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | Trading pair, e.g., BTC-USDT, please use uppercase letters |
| side | string | Yes | Order type, BUY for buy, SELL for sell |
| quantity | float64 | Yes | Order quantity, e.g., 0.1 BTC |
| limitPrice | float64 | Yes | Limit order price. e.g., 10000 USDT |
| orderPrice | float64 | Yes | The limit order price set after a stop-limit order is triggered. e.g., 10000 USDT |
| triggerPrice | float64 | Yes | The trigger price of the stop-limit order. e.g., 10000 USDT |
| listClientOrderId | string | No | Custom unique ID for the entire Order List, only supports numeric strings, e.g., "123456" |
| aboveClientOrderId | string | No | Custom unique ID for the limit order, only supports numeric strings, e.g., "123456" |
| belowClientOrderId | string | No | Custom unique ID for the stop-limit order, only supports numeric strings, e.g., "123456" |
| recvWindow | float64 | No | Request validity time window, in milliseconds |
| timestamp | int64 | Yes | Request timestamp, in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| orderId | string | Order ID |
| clientOrderId | string | Custom order ID |
| orderType | string | ocoLimit: OCO Limit Order, ocoTps: OCO Stop-Limit Order |
| symbol | string | Trading pair |
| price | float64 | Order price |
| triggerPrice | float64 | Trigger price |
| quantity | float64 | Order quantity |
| status | string | Order status, NEW for new order, PENDING for pending, PARTIALLY_FILLED for partially filled, FILLED for fully filled, CANCELED for canceled, FAILED for failed |
| side | string | Order type, BUY for buy, SELL for sell |

**Request Example**

```json
{
  "symbol": "BTC-USDT",
  "side": "BUY",
  "quantity": 0.001,
  "listClientOrderId": "12345610030",
  "aboveClientOrderId": "12345610031",
  "belowClientOrderId": "12345610031",
  "orderPrice": 88000,
  "limitPrice": 48000,
  "triggerPrice": 87000,
  "timestamp": 1724655430675
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "debugMsg": "",
  "data": [
    {
      "transactionTime": 0,
      "orderId": "1827963624962916352",
      "clientOrderId": "12345610034",
      "symbol": "BTC-USDT",
      "orderType": "ocoLimit",
      "side": "BUY",
      "triggerPrice": 0,
      "price": 48000,
      "quantity": 0.001,
      "orderListId": "12345610033",
      "status": ""
    },
    {
      "transactionTime": 0,
      "orderId": "1827963624962916353",
      "clientOrderId": "12345610035",
      "symbol": "BTC-USDT",
      "orderType": "ocoTps",
      "side": "BUY",
      "triggerPrice": 87000,
      "price": 88000,
      "quantity": 0.001,
      "orderListId": "12345610033",
      "status": ""
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/spot/v1/oco/order'
    method = "POST"
    paramsMap = {
    "symbol": "BTC-USDT",
    "side": "BUY",
    "quantity": 0.001,
    "listClientOrderId": "12345610030",
    "aboveClientOrderId": "12345610031",
    "belowClientOrderId": "12345610031",
    "orderPrice": 88000,
    "limitPrice": 48000,
    "triggerPrice": 87000,
    "timestamp": 1724655430675
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Cancel an OCO Order List

**POST** `/openApi/spot/v1/oco/cancel`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| orderId | string | No | The order ID of the limit order or the stop-limit order. Either orderId or clientOrderId must be provided. |
| clientOrderId | string | No | The User-defined order ID of the limit order or the stop-limit order |
| recvWindow | int64 | No | Request validity window, in milliseconds |
| timestamp | int64 | Yes | Request timestamp, in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| orderId | string | Order ID |
| clientOrderId | string | User-defined order ID |

**Request Example**

```json
{
  "orderId": "1735964079647111280",
  "clientOrderId": "123456789",
  "symbol": "BTC-USDT",
  "timestamp": 1702721073626
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "debugMsg": "",
  "data": {
    "orderId": "1827980248763858944",
    "clientOrderId": "123456789"
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/spot/v1/oco/cancel'
    method = "POST"
    paramsMap = {
    "orderId": "1735964079647111280",
    "clientOrderId": "123456789",
    "symbol": "BTC-USDT",
    "timestamp": 1702721073626
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query an OCO Order List

**GET** `/openApi/spot/v1/oco/orderList`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| orderListId | string | No | OCO order group ID. Either `orderListId` or `clientOrderId` must be filled in. |
| clientOrderId | string | No | User-defined OCO order group ID |
| recvWindow | int64 | No | Request valid time window, in milliseconds |
| timestamp | int64 | Yes | Request timestamp, in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| transactionTime | int64 | Order time |
| orderId | string | Order ID |
| clientOrderId | string | User-defined order ID |
| symbol | string | Trading pair |
| orderType | string | ocoLimit: OCO limit order, ocoTps: OCO stop-limit order |
| side | string | Order type, BUY for buy, SELL for sell |
| triggerPrice | float64 | Trigger price |
| price | float64 | Order price |
| quantity | float64 | Order quantity |
| orderListId | string | OCO order group ID |

**Request Example**

```json
{
  "clientOrderId": "12345610027",
  "orderListId": "1827968196914479104",
  "timestamp": 1702721583560
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "debugMsg": "",
  "data": [
    {
      "transactionTime": 1724656554890,
      "orderId": "1827968197060460545",
      "clientOrderId": "",
      "symbol": "BTC-USDT",
      "orderType": "ocoTps",
      "side": "BUY",
      "triggerPrice": 87000,
      "price": 88000,
      "quantity": 0.001,
      "orderListId": "1827968196914479104"
    },
    {
      "transactionTime": 1724656554890,
      "orderId": "1827968197060460544",
      "clientOrderId": "",
      "symbol": "BTC-USDT",
      "orderType": "ocoLimit",
      "side": "BUY",
      "triggerPrice": 0,
      "price": 48000,
      "quantity": 0.001,
      "orderListId": "1827968196914479104"
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/spot/v1/oco/orderList'
    method = "GET"
    paramsMap = {
    "clientOrderId": "12345610027",
    "orderListId": "1827968196914479104",
    "timestamp": 1702721583560
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query All Open OCO Orders

**GET** `/openApi/spot/v1/oco/openOrderList`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| pageIndex | int64 | Yes | Page number |
| pageSize | int64 | Yes | Number of items per page |
| recvWindow | int64 | No | Request validity window, in milliseconds |
| timestamp | int64 | Yes | Request timestamp, in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| transactionTime | int64 | Order time |
| orderId | string | Order ID |
| clientOrderId | string | User-defined order ID |
| symbol | string | Trading pair |
| orderType | string | ocoLimit: OCO Limit Order, ocoTps: OCO Stop-Limit Order |
| side | string | Trade type, BUY for buy, SELL for sell |
| triggerPrice | float64 | Trigger price |
| price | float64 | Order price |
| quantity | float64 | Order quantity |
| orderListId | string | OCO order group ID |

**Request Example**

```json
{
  "pageIndex": 1,
  "pageSize": 100,
  "timestamp": 1702721583560
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "debugMsg": "",
  "data": [
    {
      "transactionTime": 1724656554890,
      "orderId": "1827968197060460545",
      "clientOrderId": "",
      "symbol": "BTC-USDT",
      "orderType": "ocoTps",
      "side": "BUY",
      "triggerPrice": 87000,
      "price": 88000,
      "quantity": 0.001,
      "orderListId": "1827968196914479104",
      "status": "NEW"
    },
    {
      "transactionTime": 1724656554890,
      "orderId": "1827968197060460544",
      "clientOrderId": "",
      "symbol": "BTC-USDT",
      "orderType": "ocoLimit",
      "side": "BUY",
      "triggerPrice": 0,
      "price": 48000,
      "quantity": 0.001,
      "orderListId": "1827968196914479104",
      "status": "PENDING"
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/spot/v1/oco/openOrderList'
    method = "GET"
    paramsMap = {
    "pageIndex": 1,
    "pageSize": 100,
    "timestamp": 1702721583560
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query OCO Historical Order List

**GET** `/openApi/spot/v1/oco/historyOrderList`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| pageIndex | int64 | Yes | Page number |
| pageSize | int64 | Yes | Number of items per page |
| startTime | int64 | No | Start time, timestamp, in milliseconds |
| endTime | int64 | No | End time, timestamp, in milliseconds |
| recvWindow | int64 | No | Request validity window, in milliseconds |
| timestamp | int64 | Yes | Request timestamp, in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| transactionTime | int64 | Order time |
| orderId | string | Order ID |
| clientOrderId | string | User-defined order ID |
| symbol | string | Trading pair |
| orderType | string | ocoLimit: OCO Limit Order, ocoTps: OCO Stop-Limit Order |
| side | string | Trade type, BUY for buy, SELL for sell |
| triggerPrice | float64 | Trigger price |
| price | float64 | Order price |
| quantity | float64 | Order quantity |
| orderListId | string | OCO order group ID |

**Request Example**

```json
{
  "startTime": 1724256000000,
  "endTime": 1724342400000,
  "pageIndex": 1,
  "pageSize": 100,
  "timestamp": 1702721583560
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "debugMsg": "",
  "data": [
    {
      "transactionTime": 1724297880000,
      "orderId": "1826458150027395073",
      "clientOrderId": "",
      "symbol": "BTC-USDT",
      "orderType": "ocoTps",
      "side": "BUY",
      "triggerPrice": 64000,
      "price": 65000,
      "quantity": 0.001,
      "orderListId": "1826458148019142656",
      "status": "FAILED"
    },
    {
      "transactionTime": 1724297880000,
      "orderId": "1826458150027395072",
      "clientOrderId": "",
      "symbol": "BTC-USDT",
      "orderType": "ocoLimit",
      "side": "BUY",
      "triggerPrice": 0,
      "price": 48000,
      "quantity": 0.001,
      "orderListId": "1826458148019142656",
      "status": "CANCELED"
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/spot/v1/oco/historyOrderList'
    method = "GET"
    paramsMap = {
    "startTime": 1724256000000,
    "endTime": 1724342400000,
    "pageIndex": 1,
    "pageSize": 100,
    "timestamp": 1702721583560
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Websocket Market Data

#### Subscription transaction by transaction

**Push Data Fields**

| ENV | HOST |
|---|---|

**Connection Example**

```
{
  "id": "24dd0e35-56a4-4f7a-af8a-394c7060909c",
  "reqType": "sub",
  "dataType": "BTC-USDT@trade"
}
```

---

#### K-line Streamst

**Push Data Fields**

| ENV | HOST |
|---|---|

**Connection Example**

```
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "reqType": "sub",
  "dataType": "BTC-USDT@depth5@500ms"
}
```

---

#### Subscribe Market Depth Data

**Push Data Fields**

| ENV | HOST |
|---|---|

**Connection Example**

```
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "reqType": "sub",
  "dataType": "BTC-USDT@depth5@500ms"
}
```

---

#### Subscribe to 24-hour Price Change

**Push Data Fields**

| ENV | HOST |
|---|---|

**Connection Example**

```
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "reqType": "sub",
  "dataType": "BTC-USDT@depth5@500ms"
}
```

---

#### Spot Latest Trade Price

**Push Data Fields**

| ENV | HOST |
|---|---|

**Connection Example**

```
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "reqType": "sub",
  "dataType": "BTC-USDT@lastPrice"
}
```

---

#### Spot Best Order Book

**Push Data Fields**

| ENV | HOST |
|---|---|

**Connection Example**

```
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "reqType": "sub",
  "dataType": "BTC-USDT@bookTicker"
}
```

---

#### Incremental and Full Depth Information

**Push Data Fields**

| ENV | HOST |
|---|---|

**Connection Example**

```
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "reqType": "sub",
  "dataType": "BTC-USDT@incrDepth"
}
```

---

#### Websocket Account Data

#### order update event

**Push Data Fields**

| ENV | HOST |
|---|---|

**Connection Example**

```
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "reqType": "sub",
  "dataType": "spot.executionReport"
}
```

---

#### Subscription account balance push

WSS
Subscription account balance push
Subscription Type
dataType: ACCOUNT_UPDATE
Subscription example
{"id":"gdfg2311-d0f6-4a70-8d5a-043e4c741b40","reqType":"sub","dataType":"ACCOUNT_UPDATE"}
The field "m" represents the reason for the launch of the event, including the following possible types: INIT, DEPOSIT, WITHDRAW, ORDER, FUNDING_FEE, WITHDRAW_REJECT, ADJUSTMENT, INSURANCE_CLEAR, ADMIN_DEPOSIT, ADMIN_WITHDRAW, MARGIN_TRANSFER, MARGIN_TYPE_CHANGE, ASSET_TRANSFER, OPTIONS_PREMIUM_FEE, OPTIONS_SETTLE_PROFIT, AUTO_EXCHANGE
For more about return error codes, please see the error code description on the homepage.
The effective time of the listen key is 1 hour. In order to ensure that your subscription is not interrupted, please update the listen key regularly.
subscription address
ENV	HOST
PROD
	
wss://open-api-ws.bingx.com/market


VST
	
subscription parameters
subscription parameter	data type	description	values
id
	
string
	
subscribe id
	


reqType
	
string
	
subscribe type
	
sub/unsub


dataType
	
string
	
data type
	
ACCOUNT_UPDATE
data update
parameter	data type	description
a
	
string
	
Asset name


bc
	
string
	
Amount of asset account change this time


cw
	
string
	
Total account assets after asset account change


wb
	
string
	
Total account assets after asset account change


lk
	
string
	
Frozen assets
subscribe sample
Copy Code
{
  "id": "gdfg2311-d0f6-4a70-8d5a-043e4c741b40",
  "reqType": "sub",
  "dataType": "ACCOUNT_UPDATE"
}
subscribe success sample
Copy Code
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "code": 0,
  "msg": "",
  "dataType": "",
  "data": null
}
data update sample
Copy Code
{
  "e": "ACCOUNT_UPDATE",
  "a": {
      "B": [
            {
              "a": "USDT",  // Asset name
              "bc": "0.00",  // Amount of asset account change this time
              "cw": "0.00000000999999",  // Total account assets after asset account change
              "wb": "0.00000000999999",  // Total account assets after asset account change
              "lk": "0"  // Frozen assets
            }
          ],
      "m": "INIT"
    },  // Asset name
  "E": 1760067938102
}
cancel subscribe sample
Copy Code
{
  "id": "24dd0e35-56a4-4f7a-af8a-394c7060909c",
  "reqType": "unsub",
  "dataType": "ACCOUNT_UPDATE"
}
error code
error code	error message
No Data
code demo
PythonGolangNodejsJavaC#PHP
Copy Code
                      
import json
import websocket
import gzip
import io
URL="wss://open-api-ws.bingx.com/market" 
CHANNEL= {"id":"gdfg2311-d0f6-4a70-8d5a-043e4c741b40","reqType":"sub","dataType":"ACCOUNT_UPDATE"}
class Test(object):

    def __init__(self):
        self.url = URL 
        self.ws = None

    def on_open(self, ws):
        print('WebSocket connected')
                subStr = json.dumps(CHANNEL)
        ws.send(subStr)
        print("Subscribed to :",subStr)
        
    def on_data(self, ws, string, type, continue_flag):
        compressed_data = gzip.GzipFile(fileobj=io.BytesIO(string), mode='rb')
        decompressed_data = compressed_data.read()
        utf8_data = decompressed_data.decode('utf-8')
        print(utf8_data)

    def on_message(self, ws, message):
        compressed_data = gzip.GzipFile(fileobj=io.BytesIO(message), mode='rb')
        decompressed_data = compressed_data.read()
        utf8_data = decompressed_data.decode('utf-8')
        print(utf8_data)  #this is the message you need 
        if "ping" in utf8_data:   # this is very important , if you receive 'Ping' you need to send 'pong' 
           ws.send("Pong")

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws, close_status_code, close_msg):
        print('The connection is closed!')

    def start(self):
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self.on_open,
            on_message=self.on_message,
            # on_data=self.on_data,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        self.ws.run_forever()


if __name__ == "__main__":
    test = Test()
    test.start()
                  
Subscription Address
Subscription Parameters
Data Update
Subscribe Sample
Subscribe Success Sample
Data Update Sample
Cancel Subscribe Sample
Error Code
Code Demo

---

### Coin-M Futures

#### Market Data

#### Contract Information

**GET** `/openApi/cswap/v1/market/contracts`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | trading pair, for example: BTC-USD |
| timestamp | int64 | Yes | Request timestamp, in milliseconds. |
| recvWindow | int64 | No | The window of time for which the request is valid, in milliseconds. |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int64 | Status Code |
| msg | string | Description |
| timestamp | int64 | Response time, Unit: milliseconds |
| data | List<Data> |  |

**Request Example**

```json
{}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": [
    {
      "symbol": "BTC-USD",
      "pricePrecision": 1,
      "minTickSize": "100",
      "minTradeValue": "100",
      "minQty": "1.00000000",
      "status": 1,
      "timeOnline": 1710738000000
    },
    {
      "symbol": "ETH-USD",
      "pricePrecision": 2,
      "minTickSize": "10",
      "minTradeValue": "10",
      "minQty": "1.00000000",
      "status": 1,
      "timeOnline": 1710738000000
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/cswap/v1/market/contracts'
    method = "GET"
    paramsMap = {}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Price & Current Funding Rate

**GET** `/openApi/cswap/v1/market/premiumIndex`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | trading pair, for example: BTC-USD |
| timestamp | int64 | Yes | Request timestamp, in milliseconds. |
| recvWindow | int64 | No | The window of time for which the request is valid, in milliseconds. |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int64 | Status Code |
| msg | string | Description |
| timestamp | int64 | Response time, Unit: milliseconds |
| data | List<Data> |  |

**Request Example**

```json
{
  "symbol": "BTC-USD"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "symbol": "BTC-USD",
    "markPrice": "42216.4",
    "indexPrice": "42219.9",
    "lastFundingRate": "0.00025100",
    "nextFundingTime": 1702742400000
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/cswap/v1/market/premiumIndex'
    method = "GET"
    paramsMap = {
    "symbol": "BTC-USD"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Get Swap Open Positions

**GET** `/openApi/cswap/v1/market/openInterest`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | trading pair, for example: BTC-USD |
| timestamp | int64 | Yes | Request timestamp, in milliseconds. |
| recvWindow | int64 | No | The window of time for which the request is valid, in milliseconds. |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int64 | Status Code |
| msg | string | Description |
| timestamp | int64 | Response time, Unit: milliseconds |
| data | List<Data> |  |

**Request Example**

```json
{
  "symbol": "BTC-USD"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "openInterest": "35876.52",
    "symbol": "BTC-USD",
    "time": 1702719692859
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/cswap/v1/market/openInterest'
    method = "GET"
    paramsMap = {
    "symbol": "BTC-USD"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Get K-line Data

**GET** `/openApi/cswap/v1/market/klines`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | Trading pair, e.g., BTC-USD. Please use uppercase letters. |
| interval | string | Yes | Time interval, optional values are: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M. |
| startTime | int64 | No | Start time, the returned result includes the K-line of this time. |
| endTime | int64 | No | End time, the returned result does not include the K-line of this time. |
| timeZone | int32 | No | Time zone offset, only supports 0 or 8 (UTC+0 or UTC+8) |
| limit | int64 | No | The number of returned results. The default is 500 if not filled, and the maximum is 1000. |
| timestamp | int64 | Yes | Request timestamp, in milliseconds. |
| recvWindow | int64 | No | The window of time for which the request is valid, in milliseconds. |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int64 | Status code. |
| msg | string | Description message. |
| timestamp | int64 | Response time, Unit: milliseconds |
| data | List<Data> |  |

**Request Example**

```json
{
  "symbol": "BTC-USD",
  "interval": "1m",
  "startTime": 1716912000000,
  "endTime": 1716998400000,
  "timeZone": 8,
  "limit": 100,
  "timestamp": 1717050357477
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": [
    {
      "open": "67792.6",
      "close": "67792.6",
      "high": "67792.6",
      "low": "67792.6",
      "volume": "3.00",
      "time": 1716998340000
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/cswap/v1/market/klines'
    method = "GET"
    paramsMap = {
    "symbol": "BTC-USD",
    "interval": "1m",
    "startTime": 1716912000000,
    "endTime": 1716998400000,
    "timeZone": 8,
    "limit": 100,
    "timestamp": 1717050357477
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Depth Data

**GET** `/openApi/cswap/v1/market/depth`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | Trading pair, e.g., BTC-USD. Please use uppercase letters. |
| limit | int64 | No | The number of returned results. The default is 20 if not filled, optional values: 5, 10, 20, 50, 100, 500, 1000. |
| timestamp | int64 | Yes | Request timestamp, in milliseconds. |
| recvWindow | int64 | No | The window of time for which the request is valid, in milliseconds. |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int64 | Status code. |
| msg | string | Description message. |
| timestamp | int64 | Response time, Unit: milliseconds |
| data | List<Data> |  |

**Request Example**

```json
{
  "symbol": "BTC-USD",
  "limit": 100,
  "timestamp": 1717050357477
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "debugMsg": "",
  "data": {
    "T": 1717052420270,
    "bids": [
      [
        "67753.0",
        "1360.0"
      ],
      [
        "67752.9",
        "10.0"
      ],
      [
        "67752.8",
        "11.0"
      ],
      [
        "67752.7",
        "1.0"
      ],
      [
        "67752.6",
        "1.0"
      ]
    ],
    "asks": [
      [
        "67754.9",
        "4.0"
      ],
      [
        "67754.8",
        "4.0"
      ],
      [
        "67754.7",
        "22.0"
      ],
      [
        "67754.6",
        "19.0"
      ],
      [
        "67754.5",
        "703.0"
      ]
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/cswap/v1/market/depth'
    method = "GET"
    paramsMap = {
    "symbol": "BTC-USD",
    "limit": 100,
    "timestamp": 1717050357477
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query 24-Hour Price Change

**GET** `/openApi/cswap/v1/market/ticker`

- **Rate Limit**: IP Rate Limit IP Rate Limit :500 requests per 10 seconds.

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | Trading pair, e.g., BTC-USD. Please use uppercase letters. |
| timestamp | int64 | Yes | Request timestamp, in milliseconds. |
| recvWindow | int64 | No | The window of time for which the request is valid, in milliseconds. |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int64 | Status code. |
| msg | string | Description message. |
| timestamp | int64 | Response time, Unit: milliseconds |
| data | List<Data> |  |

**Request Example**

```json
{
  "symbol": "BTC-USD",
  "timestamp": 1717050357477
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "debugMsg": "",
  "data": [
    {
      "symbol": "BTC-USD",
      "priceChange": "-561.1",
      "priceChangePercent": "-0.8200%",
      "lastPrice": "67713.5",
      "lastQty": "38",
      "highPrice": "68346.9",
      "lowPrice": "67521.3",
      "volume": "3825668.00",
      "quoteVolume": "5084.51",
      "openPrice": "68279.2",
      "closeTime": "1717053813892",
      "bidPrice": "67712.7",
      "bidQty": "2100",
      "askPrice": "80000.0",
      "askQty": "1600"
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/cswap/v1/market/ticker'
    method = "GET"
    paramsMap = {
    "symbol": "BTC-USD",
    "timestamp": 1717050357477
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Trades Endpoints

#### Trade order

**POST** `/openApi/cswap/v1/trade/order`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | Trading pair, for example: BTC-USD, please use capital letters |
| type | string | Yes | LIMIT: Limit order/MARKET: Market order/STOP_MARKET: Market stop loss order/TAKE_PROFIT_MARKET: Market take profit order/STOP: Limit stop loss order/TAKE_PROFIT: Limit stop profit order |
| side | string | Yes | Buying and selling direction SELL, BUY |
| positionSide | string | No | Position direction, single position must fill in BOTH, two-way position can only choose LONG or SHORT, if it is empty, the default is LONG |
| price | float64 | No | Commission price |
| quantity | float64 | No | The order quantity and the number of contracts. It is not supported to place orders with U quantity at the moment. |
| stopPrice | float64 | No | Trigger price, only STOP_MARKET,TAKE_PROFIT_MARKET,STOP,TAKE_PROFIT require this parameter |
| workingType | string | No | stopPrice trigger price price type: MARK_PRICE, CONTRACT_PRICE, INDEX_PRICE, default MARK_PRICE |
| timestamp | int64 | Yes | Requested timestamp, unit: milliseconds |
| stopLoss | string | No | Support placing orders and setting stop loss at the same time. But only supports type: STOP_MARKET/STOP |
| takeProfit | string | No | Support placing orders and setting take profit at the same time. But only supports type: TAKE_PROFIT_MARKET/TAKE_PROFIT |
| clientOrderId | string | No | Request valid time window value, unit: milliseconds |
| recvWindow | int64 | No | Effective method, currently supports GTC, IOC, FOK and PostOnly |
| timeInForce | string | No | Customized order ID for users |

**Response Body**

| filed | data type | description |
|---|---|---|
| symbol | string | Trading pair, for example: BTC-USD, please use capital letters |
| side | string | Buying and selling direction SELL, BUY |
| type | string | LIMIT: Limit order/MARKET: Market order/STOP_MARKET: Market stop loss order/TAKE_PROFIT_MARKET: Market take profit order/STOP: Limit stop loss order/TAKE_PROFIT: Limit stop profit order |
| positionSide | string | Position direction, single position must fill in BOTH, two-way position can only choose LONG or SHORT, if it is empty, the default is LONG |
| orderId | int64 | order id |
| price | float64 | Commission price |
| stopPrice | float64 | Trigger price, only STOP_MARKET, TAKE_PROFIT_MARKET, STOP, TAKE_PROFIT. When type is STOP or STOP_MARKET |
| workingType | string | stopPrice trigger price price type: MARK_PRICE, CONTRACT_PRICE, INDEX_PRICE, default MARK_PRICE |
| timeInForce | string | Effective method, currently supports GTC, IOC, FOK and PostOnly |
| clientOrderId | string | Customized order ID for users |

**Request Example**

```json
{
  "symbol": "ETH-USD",
  "positionSide": "SHORT",
  "price": "3777",
  "type": "LIMIT",
  "side": "SELL",
  "quantity": "20",
  "takeProfit": "{\"type\": \"TAKE_PROFIT\", \"stopPrice\": 3666.0,\"price\": 3776.0,\"workingType\":\"CONTRACT_PRICE\"}",
  "stopLoss": "{\"type\": \"STOP\", \"stopPrice\": 3999.0,\"price\": 2888.0,\"workingType\":\"CONTRACT_PRICE\"}"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "orderId": 1802706634360750000,
    "symbol": "ETH-USD",
    "positionSide": "SHORT",
    "side": "SELL",
    "type": "LIMIT",
    "price": 3777,
    "quantity": 20,
    "stopPrice": 0,
    "workingType": "",
    "timeInForce": ""
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/cswap/v1/trade/order'
    method = "POST"
    paramsMap = {
    "symbol": "ETH-USD",
    "positionSide": "SHORT",
    "price": "3777",
    "type": "LIMIT",
    "side": "SELL",
    "quantity": "20",
    "takeProfit": "{\"type\": \"TAKE_PROFIT\", \"stopPrice\": 3666.0,\"price\": 3776.0,\"workingType\":\"CONTRACT_PRICE\"}",
    "stopLoss": "{\"type\": \"STOP\", \"stopPrice\": 3999.0,\"price\": 2888.0,\"workingType\":\"CONTRACT_PRICE\"}"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Trade Commission Rate

**GET** `/openApi/cswap/v1/user/commissionRate`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| timestamp | int64 | Yes | Request timestamp, unit: millisecond |
| recvWindow | int64 | No | Request valid time window, unit: millisecond |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int32 | Status Code |
| msg | string | Description |
| timestamp | int64 | Response Generated Time Point, unit: millisecond |
| data | List<Data> |  |

**Request Example**

```json
{}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "timestamp": 1718353924453,
  "data": {
    "takerCommissionRate": "0.0004",
    "makerCommissionRate": "0.00013999"
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/cswap/v1/user/commissionRate'
    method = "GET"
    paramsMap = {}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Leverage

**GET** `/openApi/cswap/v1/trade/leverage`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | Trading pair, e.g. BTC-USD, use uppercase letters |
| timestamp | int64 | Yes | Request timestamp, unit: millisecond |
| recvWindow | int64 | No | Request valid time window value, unit: millisecond |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int32 | Status code |
| msg | string | Description |
| timestamp | int64 | Response generation timestamp, unit: millisecond |
| data | List<Data> |  |

**Request Example**

```json
{
  "symbol": "BTC-USD"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "timestamp": 1718354677397,
  "data": {
    "symbol": "BTC-USD",
    "longLeverage": 4,
    "shortLeverage": 8,
    "maxLongLeverage": 150,
    "maxShortLeverage": 150,
    "availableLongVol": "15000000",
    "availableShortVol": "15000000"
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/cswap/v1/trade/leverage'
    method = "GET"
    paramsMap = {
    "symbol": "BTC-USD"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Modify Leverage

**POST** `/openApi/cswap/v1/trade/leverage`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | Trading pair, for example: BTC-USD, use capital letters |
| side | string | Yes | For dual-position mode, the leverage rate of long or short positions. LONG represents long position, SHORT represents short position |
| leverage | string | Yes | Leverage rate |
| timestamp | int64 | Yes | Request timestamp, unit: millisecond |
| recvWindow | int64 | No | Request valid time window value, unit: millisecond |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int32 | Status code |
| msg | string | Description |
| timestamp | int64 | Response generation timestamp, unit: millisecond |
| data | List<Data> |  |

**Request Example**

```json
{
  "symbol": "BTC-USD",
  "side": "LONG",
  "leverage": "4"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "timestamp": 1718354677397,
  "data": {
    "symbol": "BTC-USD",
    "longLeverage": 4,
    "shortLeverage": 8,
    "maxLongLeverage": 150,
    "maxShortLeverage": 150,
    "availableLongVol": "15000000",
    "availableShortVol": "15000000"
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/cswap/v1/trade/leverage'
    method = "POST"
    paramsMap = {
    "symbol": "BTC-USD",
    "side": "LONG",
    "leverage": "4"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Cancel all orders

**DELETE** `/openApi/cswap/v1/trade/allOpenOrders`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | Trading pair, example: BTC-USD, use uppercase letters |
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int32 | Status code |
| msg | string | Description |
| timestamp | int64 | Response generation time point, unit: milliseconds |
| data | Obj<Data> |  |

**Request Example**

```json
{
  "symbol": "BTC-USD"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "timestamp": 1718372477371,
  "data": {
    "success": [
      {
        "symbol": "BTC-USD",
        "orderId": "1801610628516806656",
        "side": "BUY",
        "positionSide": "LONG",
        "type": "LIMIT",
        "quantity": 2,
        "origQty": "0",
        "price": "27173",
        "executedQty": "0",
        "avgPrice": "0",
        "cumQuote": "0",
        "stopPrice": "",
        "profit": "0.0000",
        "commission": "0.000000",
        "status": "CANCELLED",
        "time": 1718372420802,
        "updateTime": 1718372420820,
        "clientOrderId": "",
        "leverage": "",
        "takeProfit": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": "",
          "stopGuaranteed": ""
        },
        "stopLoss": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": "",
          "stopGuaranteed": ""
        },
        "advanceAttr": 0,
        "positionID": 0,
        "takeProfitEntrustPrice": 0,
        "stopLossEntrustPrice": 0,
        "orderType": "",
        "workingType": ""
      }
    ],
    "failed": [
      {
        "orderId": "1801610628516806656",
        "code": 123,
        "msg": ""
      },
      {
        "orderId": "1801610628516806656",
        "code": 123,
        "msg": ""
      }
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/cswap/v1/trade/allOpenOrders'
    method = "DELETE"
    paramsMap = {
    "symbol": "BTC-USD"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Close all positions in bulk

**POST** `/openApi/cswap/v1/trade/closeAllPositions`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | Trading pair, e.g. BTC-USD, use uppercase letters |
| timestamp | int64 | Yes | Request timestamp, unit: millisecond |
| recvWindow | int64 | No | Request valid time window value, unit: millisecond |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int32 | Status code |
| msg | string | Description |
| timestamp | int64 | Response generation timestamp, unit: millisecond |
| data | Obj<Data> |  |

**Request Example**

```json
{
  "symbol": "BTC-USD"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "timestamp": 1718434280880,
  "data": {
    "success": [
      "1801870087554072576"
    ],
    "failed": [
      {
        "positionId": "12345678910111234",
        "errCode": 123,
        "errorMsg": "balabala"
      }
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/cswap/v1/trade/closeAllPositions'
    method = "POST"
    paramsMap = {
    "symbol": "BTC-USD"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query warehouse

**GET** `/openApi/cswap/v1/user/positions`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | Trading pair, example: BTC-USD, use uppercase letters |
| timestamp | int64 | Yes | Request time stamp, unit: millisecond |
| recvWindow | int64 | No | Request valid time window value, unit: millisecond |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int32 | Status code |
| msg | string | Description information |
| timestamp | int64 | Response generation time point, unit: millisecond |
| data | List<Data> | Warehouse list |

**Request Example**

```json
{
  "symbol": "BTC-USD"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": [
    {
      "symbol": "BTC-USD",
      "positionId": 1801165371278884900,
      "positionSide": "LONG",
      "isolated": false,
      "positionAmt": "3",
      "availableAmt": "3",
      "unrealizedProfit": "-0.00010485",
      "initialMargin": "0.00110845",
      "liquidationPrice": 2024.7812708419876,
      "avgPrice": "67662",
      "leverage": 4,
      "markPrice": "66098.9",
      "riskRate": "0.00013841",
      "maxMarginReduction": "0",
      "updateTime": 1718409600901
    },
    {
      "symbol": "ETH-USD",
      "positionId": 1796163366063964200,
      "positionSide": "LONG",
      "isolated": false,
      "positionAmt": "376",
      "availableAmt": "376",
      "unrealizedProfit": "-0.08051938",
      "initialMargin": "0.19994044",
      "liquidationPrice": 630.4805786791729,
      "avgPrice": "3761.12",
      "leverage": 5,
      "markPrice": "3480.77",
      "riskRate": "0.00096807",
      "maxMarginReduction": "0",
      "updateTime": 1718409600705
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/cswap/v1/user/positions'
    method = "GET"
    paramsMap = {
    "symbol": "BTC-USD"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Account Assets

**GET** `/openApi/cswap/v1/user/balance`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | Trading pair, e.g. BTC-USD, use uppercase letters |
| timestamp | int64 | Yes | Request timestamp, unit: millisecond |
| recvWindow | int64 | No | Request valid time window value, unit: millisecond |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int32 | Status code |
| msg | string | Description message |
| timestamp | int64 | Response generation time point, unit: millisecond |
| data | List<Data> | Asset list |

**Request Example**

```json
{
  "symbol": "BTC-USD"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "timestamp": 1718421301887,
  "data": [
    {
      "asset": "BTC",
      "balance": "0.14438227",
      "equity": "0.14428116",
      "unrealizedProfit": "-0.0001011",
      "availableMargin": "0.14317271",
      "usedMargin": "0.00110845",
      "freezedMargin": "0",
      "shortUid": "12345678"
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/cswap/v1/user/balance'
    method = "GET"
    paramsMap = {
    "symbol": "BTC-USD"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query force orders

**GET** `/openApi/cswap/v1/trade/forceOrders`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | Trading pair, for example: BTC-USD, use uppercase letters |
| autoCloseType | string | No | LIQUIDATION:Force order, ADL:Reduce order |
| startTime | int64 | No | Start time, unit: milliseconds |
| endTime | int64 | No | End time, unit: milliseconds |
| limit | int64 | No | The number of results in the returned result set, default value: 50, maximum value: 100 |
| timestamp | int64 | Yes | Request time stamp, unit: milliseconds |
| recvWindow | int64 | No | Request effective time window value, unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int32 | Status code |
| msg | string | Description information |
| timestamp | int64 | Response generation time point, unit: milliseconds |
| data | List<Data> | Force order list |

**Request Example**

```json
{
  "symbol": "BTC-USD"
}
```

**Response Example**

```json
{}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/cswap/v1/trade/forceOrders'
    method = "GET"
    paramsMap = {
    "symbol": "BTC-USD"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Order Trade Detail

**GET** `/openApi/cswap/v1/trade/allFillOrders`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| orderId | string | Yes | Order ID |
| pageIndex | int64 | No | Page number, default 1 |
| pageSize | int64 | No | Number per page, default 100, max 1000 |
| timestamp | int64 | Yes | Request timestamp, unit: millisecond |
| recvWindow | int64 | No | Request valid time window value, unit: millisecond |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int32 | Status code |
| msg | string | Description |
| timestamp | int64 | Response generated timestamp point, unit: millisecond |
| data | List<Data> | Trade detail list |

**Request Example**

```json
{
  "orderId": "1796163365782945792"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "timestamp": 1718423719019,
  "data": [
    {
      "orderId": "1796163365782945792",
      "symbol": "ETH-USD",
      "type": "MARKET",
      "side": "BUY",
      "positionSide": "LONG",
      "tradeId": "20789331",
      "volume": "376",
      "baseQty": 0,
      "tradePrice": "3761.12",
      "amount": "3760.00000000",
      "realizedPnl": "0.00000000",
      "commission": "-0.00039988",
      "currency": "ETH",
      "buyer": true,
      "maker": false,
      "tradeTime": 1717073692000
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/cswap/v1/trade/allFillOrders'
    method = "GET"
    paramsMap = {
    "orderId": "1796163365782945792"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Cancel an Order

**DELETE** `/openApi/cswap/v1/trade/cancelOrder`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| orderId | int64 | No | Order ID |
| symbol | string | Yes | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USD |
| clientOrderId | string | No | Customized order ID for users |
| timestamp | int64 | Yes | request timestamp, unit: millisecond |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| time | int64 | order time, unit: millisecond |
| symbol | string | trading pair, for example: BTC-USD |
| side | string | buying and selling direction |
| type | string | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order |
| positionSide | string | position side |
| cumQuote | string | transaction amount |
| status | string | order status |
| stopPrice | string | Trigger price |
| price | string | Price |
| origQty | string | original order quantity |
| avgPrice | string | average transaction price |
| executedQty | string | volume |
| orderId | int64 | Order ID |
| profit | string | profit and loss |
| commission | string | Fee |
| updateTime | int64 | update time, unit: millisecond |
| clientOrderId | string | Customized order ID for users |

**Request Example**

```json
{
  "orderId": "1736011869418901234",
  "symbol": "BTC-USD"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "order": {
      "symbol": "BTC-USDT",
      "orderId": 1736011869418901200,
      "side": "BUY",
      "positionSide": "LONG",
      "type": "LIMIT",
      "origQty": "3",
      "price": "4.5081",
      "executedQty": "0",
      "avgPrice": "0.0000",
      "cumQuote": "0",
      "stopPrice": "",
      "profit": "0.0000",
      "commission": "0.000000",
      "status": "CANCELLED",
      "time": 1702732457867,
      "updateTime": 1702732457888,
      "leverage": "",
      "takeProfit": {
        "type": "",
        "quantity": 0,
        "stopPrice": 0,
        "price": 0,
        "workingType": ""
      },
      "stopLoss": {
        "type": "",
        "quantity": 0,
        "stopPrice": 0,
        "price": 0,
        "workingType": ""
      },
      "advanceAttr": 0,
      "positionID": 0,
      "takeProfitEntrustPrice": 0,
      "stopLossEntrustPrice": 0,
      "orderType": "",
      "workingType": ""
    }
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/cswap/v1/trade/cancelOrder'
    method = "DELETE"
    paramsMap = {
    "orderId": "1736011869418901234",
    "symbol": "BTC-USD"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query all current pending orders

**GET** `/openApi/cswap/v1/trade/openOrders`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USD,When not filled, query all pending orders. When filled, query the pending orders for the corresponding currency pair |
| timestamp | int64 | Yes | request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| time | int64 | order time, unit: millisecond |
| symbol | string | trading pair, for example: BTC-USD |
| side | string | buying and selling direction |
| type | string | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order/ TRIGGER_REVERSE_MARKET:trigger reverse Market order |
| positionSide | string | Position direction, required for single position as BOTH, for both long and short positions only LONG or SHORT can be chosen, defaults to LONG if empty |
| reduceOnly | string | true, false; Default value is false for single position mode; This parameter is not accepted for both long and short positions mode |
| cumQuote | string | transaction amount |
| status | string | order status |
| stopPrice | string | Trigger price |
| price | string | Price |
| origQty | string | original order quantity |
| avgPrice | string | average transaction price |
| executedQty | string | volume |
| orderId | int64 | Order ID |
| profit | string | profit and loss |
| commission | string | Fee |
| workingType | string | StopPrice trigger price types: MARK_PRICE, CONTRACT_PRICE, INDEX_PRICE, default MARK_PRICE |
| updateTime | int64 | update time, unit: millisecond |
| timeInForce | string | Maker only |
| clientOrderId | string | Effective method, currently supports GTC, IOC, FOK and PostOnly |

**Request Example**

```json
{
  "symbol": "BTC-USD"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "orders": [
      {
        "symbol": "BTC-USD",
        "orderId": 1733405587011123500,
        "side": "SELL",
        "positionSide": "LONG",
        "type": "LIMIT",
        "origQty": "0.0030",
        "price": "44459.6",
        "executedQty": "0.0000",
        "avgPrice": "0.0",
        "cumQuote": "0",
        "stopPrice": "",
        "profit": "0.0",
        "commission": "0.0",
        "status": "PENDING",
        "time": 1702256915574,
        "updateTime": 1702256915610,
        "clientOrderId": "",
        "leverage": "",
        "takeProfit": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": "",
          "StopGuaranteed": ""
        },
        "stopLoss": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": "",
          "StopGuaranteed": ""
        },
        "positionID": 0,
        "takeProfitEntrustPrice": 0,
        "stopLossEntrustPrice": 0,
        "orderType": "",
        "postOnly": false,
        "workingType": "MARK_PRICE"
      },
      {
        "symbol": "BTC-USDT",
        "orderId": 1733405587011123500,
        "side": "SELL",
        "positionSide": "LONG",
        "type": "LIMIT",
        "origQty": "0.0030",
        "price": "44454.6",
        "executedQty": "0.0000",
        "avgPrice": "0.0",
        "cumQuote": "0",
        "stopPrice": "",
        "profit": "0.0",
        "commission": "0.0",
        "status": "PENDING",
        "time": 1702111071719,
        "updateTime": 1702111071735,
        "clientOrderId": "",
        "leverage": "",
        "takeProfit": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": "",
          "StopGuaranteed": ""
        },
        "stopLoss": {
          "type": "",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": "",
          "StopGuaranteed": ""
        },
        "positionID": 0,
        "takeProfitEntrustPrice": 0,
        "stopLossEntrustPrice": 0,
        "orderType": "",
        "postOnly": false,
        "workingType": "MARK_PRICE"
      }
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/cswap/v1/trade/openOrders'
    method = "GET"
    paramsMap = {
    "symbol": "BTC-USD"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Order

**GET** `/openApi/cswap/v1/trade/orderDetail`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USD |
| orderId | int64 | No | Order ID |
| clientOrderId | string | No | Customized order ID for users |
| timestamp | int64 | Yes | request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| time | int64 | order time, unit: millisecond |
| symbol | string | trading pair, for example: BTC-USDT |
| side | string | buying and selling direction |
| type | string | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order |
| positionSide | string | Position direction, required for single position as BOTH, for both long and short positions only LONG or SHORT can be chosen, defaults to LONG if empty |
| reduceOnly | string | true, false; Default value is false for single position mode; This parameter is not accepted for both long and short positions mode |
| cumQuote | string | transaction amount |
| status | string | order status |
| stopPrice | string | Trigger price |
| price | string | Price |
| origQty | string | original order quantity |
| avgPrice | string | average transaction price |
| executedQty | string | volume |
| orderId | int64 | Order ID |
| profit | string | profit and loss |
| commission | string | Fee |
| updateTime | int64 | update time, unit: millisecond |
| workingType | string | StopPrice trigger price types: MARK_PRICE, CONTRACT_PRICE, INDEX_PRICE, default MARK_PRICE |
| timeInForce | string | Effective method, currently supports GTC, IOC, FOK and PostOnly |
| clientOrderId | string | Customized order ID for users |

**Request Example**

```json
{
  "orderId": "1736012449498123456",
  "symbol": "OP-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "order": {
      "symbol": "OP-USD",
      "orderId": 1736012449498123500,
      "side": "SELL",
      "positionSide": "LONG",
      "type": "LIMIT",
      "origQty": "1.0",
      "price": "2.1710",
      "executedQty": "0.0",
      "avgPrice": "0.0000",
      "cumQuote": "0",
      "stopPrice": "",
      "profit": "0.0000",
      "commission": "0.000000",
      "status": "PENDING",
      "time": 1702732596168,
      "updateTime": 1702732596188,
      "leverage": "",
      "takeProfit": {
        "type": "",
        "quantity": 0,
        "stopPrice": 0,
        "price": 0,
        "workingType": ""
      },
      "stopLoss": {
        "type": "",
        "quantity": 0,
        "stopPrice": 0,
        "price": 0,
        "workingType": ""
      },
      "advanceAttr": 0,
      "positionID": 0,
      "takeProfitEntrustPrice": 0,
      "stopLossEntrustPrice": 0,
      "orderType": "",
      "workingType": "MARK_PRICE"
    }
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/cswap/v1/trade/orderDetail'
    method = "GET"
    paramsMap = {
    "orderId": "1736012449498123456",
    "symbol": "OP-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### User's History Orders

**GET** `/openApi/cswap/v1/trade/orderHistory`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USD.If no symbol is specified, it will query the historical orders for all trading pairs. |
| orderId | int64 | No | Only return subsequent orders, and return the latest order by default |
| startTime | int64 | No | Start time, unit: millisecond |
| endTime | int64 | No | End time, unit: millisecond |
| limit | int64 | Yes | number of result sets to return Default: 500 Maximum: 1000 |
| timestamp | int64 | Yes | request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| time | int64 | order time, unit: millisecond |
| symbol | string | trading pair, for example: BTC-USDT.If a specific pair is not provided, a history of transactions for all pairs will be returned |
| side | string | buying and selling direction |
| type | string | LIMIT: Limit Order / MARKET: Market Order / STOP_MARKET: Stop Market Order / TAKE_PROFIT_MARKET: Take Profit Market Order / STOP: Stop Limit Order / TAKE_PROFIT: Take Profit Limit Order / TRIGGER_LIMIT: Stop Limit Order with Trigger / TRIGGER_MARKET: Stop Market Order with Trigger / TRAILING_STOP_MARKET: Trailing Stop Market Order |
| positionSide | string | Position direction, required for single position as BOTH, for both long and short positions only LONG or SHORT can be chosen, defaults to LONG if empty |
| reduceOnly | string | true, false; Default value is false for single position mode; This parameter is not accepted for both long and short positions mode |
| cumQuote | string | transaction amount |
| status | string | order status |
| stopPrice | string | Trigger price |
| price | string | Price |
| origQty | string | original order quantity |
| avgPrice | string | average transaction price |
| executedQty | string | volume |
| orderId | int64 | Order ID |
| profit | string | profit and loss |
| commission | string | Fee |
| updateTime | int64 | StopPrice trigger price types: MARK_PRICE, CONTRACT_PRICE, INDEX_PRICE, default MARK_PRICE |
| workingType | string | update time, unit: millisecond |
| timeInForce | string | Effective method, currently supports GTC, IOC, FOK and PostOnly |
| clientOrderId | string | Customized order ID for users |

**Request Example**

```json
{
  "endTime": "1702731995000",
  "limit": "500",
  "startTime": "1702688795000",
  "symbol": "PYTH-USD"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "orders": [
      {
        "symbol": "PYTH-USD",
        "orderId": 1736007506620112100,
        "side": "SELL",
        "positionSide": "SHORT",
        "type": "LIMIT",
        "origQty": "33",
        "price": "0.3916",
        "executedQty": "33",
        "avgPrice": "0.3916",
        "cumQuote": "13",
        "stopPrice": "",
        "profit": "0.0000",
        "commission": "-0.002585",
        "status": "FILLED",
        "time": 1702731418000,
        "updateTime": 1702731470000,
        "clientOrderId": "",
        "leverage": "15X",
        "takeProfit": {
          "type": "TAKE_PROFIT",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": ""
        },
        "stopLoss": {
          "type": "STOP",
          "quantity": 0,
          "stopPrice": 0,
          "price": 0,
          "workingType": ""
        },
        "advanceAttr": 0,
        "positionID": 0,
        "takeProfitEntrustPrice": 0,
        "stopLossEntrustPrice": 0,
        "orderType": "",
        "workingType": "MARK_PRICE"
      }
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/cswap/v1/trade/orderHistory'
    method = "GET"
    paramsMap = {
    "endTime": "1702731995000",
    "limit": "500",
    "startTime": "1702688795000",
    "symbol": "PYTH-USD"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Margin Type

**GET** `/openApi/swap/v2/trade/marginType`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | There must be a hyphen/ "-" in the trading pair symbol. eg: BTC-USDT |
| timestamp | int64 | Yes | request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| marginType | string | margin mode |

**Request Example**

```json
{
  "symbol": "WOO-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "data": {
    "marginType": "CROSSED"
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/marginType'
    method = "GET"
    paramsMap = {
    "symbol": "WOO-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Set Margin Type

**POST** `/openApi/cswap/v1/trade/marginType`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | Trading pair, e.g., BTC-USD, please use uppercase letters |
| marginType | string | Yes | Margin type, e.g., ISOLATED, CROSSED |
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | Request validity window in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | error msg |  |

**Request Example**

```json
{
  "symbol": "BTC-USD",
  "marginType": "ISOLATED",
  "recvWindow": "5000"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "timestamp": 1716388317402,
  "data": []
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/cswap/v1/trade/marginType'
    method = "POST"
    paramsMap = {
    "symbol": "BTC-USD",
    "marginType": "ISOLATED",
    "recvWindow": "5000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Adjust Isolated Margin

**POST** `/openApi/cswap/v1/trade/positionMargin`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | Trading pair, e.g., BTC-USD, please use uppercase letters |
| amount | float64 | Yes | Margin funds |
| type | int64 | Yes | Adjustment direction: 1: Increase isolated margin, 2: Decrease isolated margin |
| positionSide | string | Yes | Position direction, can only be LONG or SHORT |
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | Request validity window in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | int64 | Error code, 0 means success, non-0 means failure |
| msg | string | Error message |

**Request Example**

```json
{
  "recvWindow": "10000",
  "symbol": "BTC-USD",
  "type": "Increase",
  "amount": "0.01",
  "positionSide": "LONG"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": ""
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/cswap/v1/trade/positionMargin'
    method = "POST"
    paramsMap = {
    "recvWindow": "10000",
    "symbol": "BTC-USD",
    "type": "Increase",
    "amount": "0.01",
    "positionSide": "LONG"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Websocket Market Data

#### Subscription transaction by transaction

**Push Data Fields**

| ENV | HOST |
|---|---|

**Connection Example**

```
{
  "id": "24dd0e35-56a4-4f7a-af8a-394c7060909c",
  "reqType": "sub",
  "dataType": "BTC-USDT@trade"
}
```

---

#### Subscribe to the Latest Transaction Price

**Push Data Fields**

| ENV | HOST |
|---|---|

**Connection Example**

```
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "reqType": "sub",
  "dataType": "BTC-USD@lastPrice"
}
```

---

#### Subscribe to Mark Price

**Push Data Fields**

| ENV | HOST |
|---|---|

**Connection Example**

```
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "reqType": "sub",
  "dataType": "BTC-USD@markPrice"
}
```

---

#### Subscribe to Limited Depth

**Push Data Fields**

| ENV | HOST |
|---|---|

**Connection Example**

```
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "reqType": "sub",
  "dataType": "BTC-USD@depth5"
}
```

---

#### Subscribe to Best Bid and Ask

**Push Data Fields**

| ENV | HOST |
|---|---|

**Connection Example**

```
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "reqType": "sub",
  "dataType": "BTC-USD@bookTicker"
}
```

---

#### Subscribe to Latest Trading Pair K-Line

**Push Data Fields**

| ENV | HOST |
|---|---|

**Connection Example**

```
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "reqType": "sub",
  "dataType": "BTC-USD@kline_1m"
}
```

---

#### Subscribe to 24-Hour Price Change

**Push Data Fields**

| ENV | HOST |
|---|---|

**Connection Example**

```
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "reqType": "sub",
  "dataType": "BTC-USD@ticker"
}
```

---

#### Websocket Account Data

#### Account balance and position update push

WSS
Account balance and position update push
This type of event will be pushed when a new order is created, an order has a new deal, or a new status change. The event type is unified as ORDER_TRADE_UPDATE.
Order direction
BUY buy
SELL sell
Order Type
MARKET market order
TAKE_PROFIT_MARKET take profit market order
STOP_MARKET stop market order
LIMIT limit order
TAKE_PROFIT take profit limit order
STOP stop limit order
TRIGGER_MARKET stop market order with trigger
TRIGGER_LIMIT stop limit order with trigger
TRAILING_STOP_MARKET trailing stop market order
TRAILING_TP_SL trailing take profit or stop loss
LIQUIDATION strong liquidation order
The specific execution type of this event
NEW
CANCELED removed
CALCULATED order ADL or liquidation
EXPIRED order lapsed
TRADE transaction
Order Status
NEW
PARTIALLY_FILLED
FILLED
CANCELED
EXPIRED
Account data no longer need to subscribe to channel type, after connect wss://open-api-swap.bingx.com/swap-market?listenKey=a8ea75681542e66f1a50a1616dd06ed77dab61baa0c296bca03a9b13ee5f2dd7 , All event types will be pushed.
The effective time of the listen key is 1 hour. In order to ensure that your subscription is not interrupted, please update the listen key regularly.
subscription address
ENV	HOST
PROD
	
wss://open-api-swap.bingx.com/swap-market


VST
	
wss://vst-open-api-ws.bingx.com/swap-market
subscription parameters
subscription parameter	data type	description	values
No Data
No channel subscription required; only listenKey is needed.
data update
parameter	data type	description
e
	
string
	
Event type (ACCOUNT_UPDATE)


E
	
int64
	
Event time in milliseconds


T
	
int64
	
Push time in milliseconds


a
	
object
	
Account update event object


a.m
	
string
	
Reason for the account update


a.B
	
array
	
Balance information array


a.B.a
	
string
	
Asset name (e.g. USDT)


a.B.wb
	
string
	
Wallet balance


a.B.cw
	
string
	
Wallet balance excluding isolated margin


a.B.bc
	
string
	
Balance change


a.P
	
array
	
Position information array


a.P.s
	
string
	
Trading pair (e.g. LINK-USDT)


a.P.pa
	
string
	
Position amount


a.P.ep
	
string
	
Entry price


a.P.up
	
string
	
Unrealized profit and loss


a.P.mt
	
string
	
Margin mode (isolated / crossed)


a.P.iw
	
string
	
Isolated position margin


a.P.ps
	
string
	
Position side (LONG / SHORT / BOTH)


a.P.cr
	
string
	
Realized profit and loss

No channel subscription required; only listenKey is needed.

subscribe sample
Copy Code
{}
subscribe success sample
Copy Code
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "code": 0,
  "msg": "",
  "dataType": "",
  "data": null
}
data update sample
Copy Code
{
  "e": "ACCOUNT_UPDATE",  // Event type (ACCOUNT_UPDATE)
  "E": 1758608899352,  // Event time in milliseconds
  "a": {
      "m": "ORDER",  // Reason for the account update
      "B": [
            {
              "a": "USDT",  // Asset name (e.g. USDT)
              "wb": "117.80007595",  // Wallet balance
              "cw": "95.23045595",  // Wallet balance excluding isolated margin
              "bc": "0"  // Balance change
            }
          ],  // Balance information array
      "P": [
            {
              "s": "BTC-USDT",  // Trading pair (e.g. LINK-USDT)
              "pa": "0.00100000",  // Position amount
              "ep": "112848.10000000",  // Entry price
              "up": "-0.00004435",  // Unrealized profit and loss
              "mt": "cross",  // Margin mode (isolated / crossed)
              "iw": "22.56957565",  // Isolated position margin
              "ps": "SHORT",  // Position side (LONG / SHORT / BOTH)
              "cr": "-0.05642405"  // Realized profit and loss
            }
          ]  // Position information array
    }  // Account update event object
}
cancel subscribe sample
Copy Code
{}
error code
error code	error message
403
	
Internal service call exception


1006
	
Internal service call exception.Generally network related issue


80015
	
dataType not supported
code demo
PythonGolangNodejsJavaC#PHP
Copy Code
                      
import json
import websocket
import gzip
import io
URL="wss://open-api-swap.bingx.com/swap-market?listenKey=a8ea75681542e66f1a50a1616dd06ed77dab61baa0c296bca03a9b13ee5f2dd7" 

class Test(object):

    def __init__(self):
        self.url = URL 
        self.ws = None

    def on_open(self, ws):
        print('WebSocket connected')
        

    def on_data(self, ws, string, type, continue_flag):
        compressed_data = gzip.GzipFile(fileobj=io.BytesIO(string), mode='rb')
        decompressed_data = compressed_data.read()
        utf8_data = decompressed_data.decode('utf-8')
        print(utf8_data)

    def on_message(self, ws, message):
        compressed_data = gzip.GzipFile(fileobj=io.BytesIO(message), mode='rb')
        decompressed_data = compressed_data.read()
        utf8_data = decompressed_data.decode('utf-8')
        print(utf8_data)  #this is the message you need 
        if utf8_data == "Ping": # this is very important , if you receive 'Ping' you need to send 'Pong' 
           ws.send("Pong")

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws, close_status_code, close_msg):
        print('The connection is closed!')

    def start(self):
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self.on_open,
            on_message=self.on_message,
            # on_data=self.on_data,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        self.ws.run_forever()


if __name__ == "__main__":
    test = Test()
    test.start()
                  
Subscription Address
Subscription Parameters
Data Update
Subscribe Sample
Subscribe Success Sample
Data Update Sample
Cancel Subscribe Sample
Error Code
Code Demo

---

#### Order update push

WSS
Order update push
The event type of the account update event is fixed as ACCOUNT_UPDATE
When the account information changes, this event will be pushed:
This event will only be pushed when there is a change in account information (including changes in funds, positions, etc.); This event will not be pushed if the change in the order status does not cause changes in the account and positions.
Position information: push only when there is a change in the symbol position.
Fund balance changes caused by "FUNDING FEE", only push brief events:
When "FUNDING FEE" occurs in a user's cross position, the event ACCOUNT_UPDATE will only push the relevant user's asset balance information B (only push the asset balance information related to the occurrence of FUNDING FEE), and will not push any position information P.
When "FUNDING FEE" occurs in a user's isolated position, the event ACCOUNT_UPDATE will only push the relevant user asset balance information B (only push the asset balance information used by "FUNDING FEE"), and related position information P (Only the position information where this "FUNDING FEE" occurred is pushed), and the rest of the position information will not be pushed.
The field "m" represents the reason for the launch of the event, including the following possible types: DEPOSIT, WITHDRAW, ORDER, FUNDING_FEE
Account data no longer need to subscribe to channel type, after connecting wss://open-api-swap.bingx.com/swap-market?listenKey=a8ea75681542e66f1a50a1616dd06ed77dab61baa0c296bca03a9b13ee5f2dd7 , All event types will be pushed.
The effective time of the listen key is 1 hour. In order to ensure that your subscription is not interrupted, please update the listen key regularly.
subscription address
ENV	HOST
PROD
	
wss://open-api-swap.bingx.com/swap-market


VST
	
wss://vst-open-api-ws.bingx.com/swap-market
subscription parameters
subscription parameter	data type	description	values
No Data
No channel subscription required; only listenKey is needed.
data update
parameter	data type	description
s
	
string
	
Trading pair (e.g., LINK-USDT)


c
	
string
	
Client-defined order ID


i
	
int64
	
Order ID (e.g., 1627970445070303232)


S
	
string
	
Order side (BUY/SELL)


o
	
string
	
Order type (LIMIT/MARKET, etc.)


q
	
string
	
Order quantity


p
	
string
	
Order price


sp
	
string
	
Trigger price


ap
	
string
	
Average filled price


x
	
string
	
Execution type for this event (e.g., TRADE)


X
	
string
	
Current order status (NEW/PARTIALLY_FILLED/FILLED/CANCELED, etc.)


N
	
string
	
Fee asset (e.g., USDT)


n
	
string
	
Fee (may be negative)


T
	
int64
	
Trade time (timestamp in ms)


wt
	
string
	
Trigger price type: MARK_PRICE / CONTRACT_PRICE / INDEX_PRICE


ps
	
string
	
Position side: LONG / SHORT / BOTH


rp
	
string
	
Realized PnL for this trade


z
	
string
	
Cumulative filled quantity


sg
	
boolean
	
Guaranteed TP/SL enabled: true/false


ti
	
int64
	
Related conditional order ID (e.g., 1771124709866754048)


ro
	
boolean
	
Reduce-only order flag


td
	
string
	
Trade ID


tv
	
string
	
Trade value / notional

No channel subscription required; only listenKey is needed.

subscribe sample
Copy Code
{}
subscribe success sample
Copy Code
{
  "code": 0,
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "msg": "SUCCESS",
  "timestamp": 1759980142604
}
data update sample
Copy Code
{
  "e": "TRADE_UPDATE",
  "E": 1758608899350,
  "T": 1758608899316,  // Trade time (timestamp in ms)
  "o": {
      "s": "BTC-USDT",  // Trading pair (e.g., LINK-USDT)
      "c": "",  // Client-defined order ID
      "i": 1970374651259388000,  // Order ID (e.g., 1627970445070303232)
      "S": "SELL",  // Order side (BUY/SELL)
      "o": "MARKET",  // Order type (LIMIT/MARKET, etc.)
      "q": "0.00100000",  // Order quantity
      "p": "112848.10000000",  // Order price
      "sp": "0.00000000",  // Trigger price
      "ap": "112848.10000000",  // Average filled price
      "x": "TRADE",  // Execution type for this event (e.g., TRADE)
      "X": "FILLED",  // Current order status (NEW/PARTIALLY_FILLED/FILLED/CANCELED, etc.)
      "N": "USDT",  // Fee asset (e.g., USDT)
      "n": "-0.05642405",  // Fee (may be negative)
      "T": 1758608899316,  // Trade time (timestamp in ms)
      "wt": "",  // Trigger price type: MARK_PRICE / CONTRACT_PRICE / INDEX_PRICE
      "ps": "SHORT",  // Position side: LONG / SHORT / BOTH
      "rp": "0.00000000",  // Realized PnL for this trade
      "z": "0.00100000",  // Cumulative filled quantity
      "sg": "false",  // Guaranteed TP/SL enabled: true/false
      "ti": 0,  // Related conditional order ID (e.g., 1771124709866754048)
      "ro": false,  // Reduce-only order flag
      "td": 511178071,  // Trade ID
      "tv": "112.8"  // Trade value / notional
    }  // Order type (LIMIT/MARKET, etc.)
}
cancel subscribe sample
Copy Code
{}
error code
error code	error message
403
	
Internal service call exception


1006
	
Internal service call exception.Generally network related issue


80015
	
dataType not supported
code demo
PythonGolangNodejsJavaC#PHP
Copy Code
                      
import json
import websocket
import gzip
import io
URL="wss://open-api-swap.bingx.com/swap-market" 
CHANNEL= {}
class Test(object):

    def __init__(self):
        self.url = URL 
        self.ws = None

    def on_open(self, ws):
        print('WebSocket connected')
                subStr = json.dumps(CHANNEL)
        ws.send(subStr)
        print("Subscribed to :",subStr)
        
    def on_data(self, ws, string, type, continue_flag):
        compressed_data = gzip.GzipFile(fileobj=io.BytesIO(string), mode='rb')
        decompressed_data = compressed_data.read()
        utf8_data = decompressed_data.decode('utf-8')
        print(utf8_data)

    def on_message(self, ws, message):
        compressed_data = gzip.GzipFile(fileobj=io.BytesIO(message), mode='rb')
        decompressed_data = compressed_data.read()
        utf8_data = decompressed_data.decode('utf-8')
        print(utf8_data)  #this is the message you need 
        if utf8_data == "Ping": # this is very important , if you receive 'Ping' you need to send 'Pong' 
           ws.send("Pong")

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws, close_status_code, close_msg):
        print('The connection is closed!')

    def start(self):
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self.on_open,
            on_message=self.on_message,
            # on_data=self.on_data,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        self.ws.run_forever()


if __name__ == "__main__":
    test = Test()
    test.start()
                  
Subscription Address
Subscription Parameters
Data Update
Subscribe Sample
Subscribe Success Sample
Data Update Sample
Cancel Subscribe Sample
Error Code
Code Demo

---

#### Configuration updates such as leverage and margin mode

WSS
Configuration updates such as leverage and margin mode
When the account configuration changes, the event type will be pushed as ACCOUNT_CONFIG_UPDATE
When the leverage of a trading pair changes, the push message will contain the object ac, which represents the account configuration of the trading pair, where s represents the specific trading pair, l represents the leverage of long positions, S represents the leverage of short positions, and mt represents the margin mode.
For more about return error codes, please see the error code description on the homepage.
Each time a connection is successfully established, a full data push will occur once, followed by another full push every 5 seconds.
Account data no longer need to subscribe to channel type, after connecting wss://open-api-swap.bingx.com/swap-market?listenKey=a8ea75681542e66f1a50a1616dd06ed77dab61baa0c296bca03a9b13ee5f2dd7, All event types will be pushed.
The effective time of the listen key is 1 hour. In order to ensure that your subscription is not interrupted, please update the listen key regularly.
subscription address
ENV	HOST
PROD
	
wss://open-api-swap.bingx.com/swap-market


VST
	
wss://vst-open-api-ws.bingx.com/swap-market
subscription parameters
subscription parameter	data type	description	values
No Data
No channel subscription required; only listenKey is needed.
data update
parameter	data type	description
e
	
string
	
Event type (ACCOUNT_CONFIG_UPDATE)


E
	
int64
	
Event time in milliseconds


ac
	
object
	
Account configuration update object


s
	
string
	
Trading pair (e.g. BTC-USDT)


l
	
int32
	
Long position leverage


S
	
int32
	
Short position leverage


mt
	
string
	
Margin mode (cross / isolated)

No channel subscription required; only listenKey is needed.

subscribe sample
Copy Code
{}
subscribe success sample
Copy Code
{
  "id": "e745cd6d-d0f6-4a70-8d5a-043e4c741b40",
  "code": 0,
  "msg": "",
  "dataType": "",
  "data": null
}
data update sample
Copy Code
{
  "e": "ACCOUNT_CONFIG_UPDATE",  // Event type (ACCOUNT_CONFIG_UPDATE)
  "E": 1769443029713,  // Event time in milliseconds
  "ac": {
      "s": "NCCOGOLD2USD-USDT",  // Trading pair (e.g. BTC-USDT)
      "l": 412,  // Long position leverage
      "S": 428,  // Short position leverage
      "mt": "cross"  // Margin mode (cross / isolated)
    }  // Account configuration update object
}
cancel subscribe sample
Copy Code
{}
error code
error code	error message
403
	
Internal service call exception


1006
	
Internal service call exception.Generally network related issue


80015
	
dataType not supported
code demo
PythonGolangNodejsJavaC#PHP
Copy Code
                      
import json
import websocket
import gzip
import io
URL="wss://open-api-swap.bingx.com/swap-market" 
CHANNEL= {}
class Test(object):

    def __init__(self):
        self.url = URL 
        self.ws = None

    def on_open(self, ws):
        print('WebSocket connected')
                subStr = json.dumps(CHANNEL)
        ws.send(subStr)
        print("Subscribed to :",subStr)
        
    def on_data(self, ws, string, type, continue_flag):
        compressed_data = gzip.GzipFile(fileobj=io.BytesIO(string), mode='rb')
        decompressed_data = compressed_data.read()
        utf8_data = decompressed_data.decode('utf-8')
        print(utf8_data)

    def on_message(self, ws, message):
        compressed_data = gzip.GzipFile(fileobj=io.BytesIO(message), mode='rb')
        decompressed_data = compressed_data.read()
        utf8_data = decompressed_data.decode('utf-8')
        print(utf8_data)  #this is the message you need 
        if utf8_data == "Ping": # this is very important , if you receive 'Ping' you need to send 'Pong' 
           ws.send("Pong")

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws, close_status_code, close_msg):
        print('The connection is closed!')

    def start(self):
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self.on_open,
            on_message=self.on_message,
            # on_data=self.on_data,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        self.ws.run_forever()


if __name__ == "__main__":
    test = Test()
    test.start()
                  
Subscription Address
Subscription Parameters
Data Update
Subscribe Sample
Subscribe Success Sample
Data Update Sample
Cancel Subscribe Sample
Error Code
Code Demo

---

### Account and Wallet

#### Fund Account

#### Query Assets

**GET** `/openApi/spot/v1/account/balance`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| recvWindow | int64 | No | Timestamp of initiating the request, Unit: milliseconds |
| timestamp | int64 | Yes | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| balances | Array | Asset list, element fields refer to the following table |

**Request Example**

```json
{
  "recvWindow": "60000"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "debugMsg": "",
  "data": {
    "balances": [
      {
        "asset": "USDT",
        "free": "566773.193402631",
        "locked": "244.18616265388994"
      },
      {
        "asset": "CHEEMS",
        "free": "294854132046232",
        "locked": "18350553840"
      },
      {
        "asset": "VST",
        "free": "0",
        "locked": "0"
      }
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/spot/v1/account/balance'
    method = "GET"
    paramsMap = {
    "recvWindow": "60000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Asset transfer records

**GET** `/openApi/api/v3/asset/transfer`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| type | ENUM | Yes | transfer type, (query by type or tranId) |
| tranId | LONG | No | transaction ID, (query by type or tranId) |
| startTime | LONG | No | Starting time1658748648396 |
| endTime | LONG | No | End Time 1658748648396 |
| current | int64 | No | current page default1 |
| size | int64 | No | Page size default 10 can not exceed 100 |
| recvWindow | LONG | No | Execution window time, cannot be greater than 60000 |
| timestamp | LONG | Yes | current timestamp e.g.1658748648396 |

**Response Body**

| filed | data type | description |
|---|---|---|
| total | LONG | total |
| rows | Array | Array |
| asset | string | coin name |
| amount | DECIMAL | coin amount |
| type | ENUM | transfer tpye |
| status | string | CONFIRMED |
| tranId | LONG | Transaction ID |
| timestamp | LONG | Transfer time stamp |

**Request Example**

```json
{
  "type": "FUND_PFUTURES"
}
```

**Response Example**

```json
{
  "total": 2,
  "rows": [
    {
      "asset": "VST",
      "amount": "100000.00000000000000000000",
      "type": "FUND_PFUTURES",
      "status": "CONFIRMED",
      "tranId": 37600111,
      "timestamp": 1702252271000
    },
    {
      "asset": "USDT",
      "amount": "2218.72352626000000000000",
      "type": "FUND_PFUTURES",
      "status": "CONFIRMED",
      "tranId": 37600222,
      "timestamp": 1702351131000
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/api/v3/asset/transfer'
    method = "GET"
    paramsMap = {
    "type": "FUND_PFUTURES"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Main Accoun internal transfer

**POST** `/openApi/wallets/v1/capital/innerTransfer/apply`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| coin | string | Yes | Name of the transferred currency |
| userAccountType | int64 | Yes | User account type 1=UID 2=phone number 3=email |
| userAccount | string | Yes | User account: UID, phone number, email |
| amount | float64 | Yes | Transfer amount |
| callingCode | string | No | Area code for telephone, required when userAccountType=2. |
| walletType | int64 | Yes | Account type, 1 Fund Account; 2 Standard Futures Account; 3 Perpetual Futures Account; 4 Spot Account |
| transferClientId | string | No | Custom ID for internal transfer by the client, combination of numbers and letters, length less than 100 characters |
| timestamp | int64 | Yes | The timestamp of the request, in milliseconds. |
| recvWindow | int64 | No | Request validity time window, unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| id | string | The platform returns the unique ID of the internal transfer record. |
| transferClientId | string | Custom ID for internal transfer by the client, combination of numbers and letters, length less than 100 characters |

**Request Example**

```json
{
  "amount": "10.0",
  "coin": "USDT",
  "userAccount": "16779999",
  "userAccountType": "1",
  "walletType": "1"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1702558152381,
  "data": {
    "id": "12******1"
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/wallets/v1/capital/innerTransfer/apply'
    method = "POST"
    paramsMap = {
    "amount": "10.0",
    "coin": "USDT",
    "userAccount": "16779999",
    "userAccountType": "1",
    "walletType": "1"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Asset Transfer New

**POST** `/openApi/api/asset/v1/transfer`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| fromAccount | string | Yes | fromAccount, fund：Funding Account spot:Spot Account, stdFutures:Standard Contract, coinMPerp:COIN-M Perpetual Future, USDTMPerp:Perpetual Future |
| toAccount | string | Yes | toAccount, fund:Funding Account spot:Spot Account, stdFutures:Standard Contract, coinMPerp:COIN-M Perpetual Future, USDTMPerp:Perpetual Future |
| asset | string | Yes | coin name e.g. USDT |
| amount | DECIMAL | Yes | amount |
| recvWindow | LONG | No | Execution window time, cannot be greater than 60000 |
| timestamp | LONG | Yes | current timestamp e.g. 1658748648396 |

**Response Body**

| filed | data type | description |
|---|---|---|
| transferId | string | transfer ID |

**Request Example**

```json
{
  "recvWindow": "6000",
  "asset": "USDT",
  "amount": "1095",
  "fromAccount": "fund",
  "toAccount": "spot"
}
```

**Response Example**

```json
{
  "transferId": "17********28"
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/api/asset/v1/transfer'
    method = "POST"
    paramsMap = {
    "recvWindow": "6000",
    "asset": "USDT",
    "amount": "1095",
    "fromAccount": "fund",
    "toAccount": "spot"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query transferable currency

**GET** `/openApi/api/asset/v1/transfer/supportCoins`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| fromAccount | string | Yes | fromAccount, fund：Funding Account spot:Spot Account, stdFutures:Standard Contract, coinMPerp:COIN-M Perpetual Future, USDTMPerp:Perpetual Future |
| toAccount | string | Yes | toAccount, fund:Funding Account spot:Spot Account, stdFutures:Standard Contract, coinMPerp:COIN-M Perpetual Future, USDTMPerp:Perpetual Future |
| recvWindow | int64 | No | Execution window time, cannot be greater than 60000 |
| timestamp | int64 | Yes | Current timestamp e.g. 1658748648396 |

**Response Body**

| filed | data type | description |
|---|---|---|
| coins | Array | Coin Asset, element fields refer to the following table |

**Request Example**

```json
{
  "fromAccount": "spot",
  "toAccount": "fund",
  "recvWindow": "60000"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "debugMsg": "",
  "data": {
    "coins": [
      {
        "asset": "USDT",
        "amount": "566773.193402631"
      },
      {
        "asset": "CHEEMS",
        "amount": "24324.21"
      }
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/api/asset/v1/transfer/supportCoins'
    method = "GET"
    paramsMap = {
    "fromAccount": "spot",
    "toAccount": "fund",
    "recvWindow": "60000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Asset transfer records new

**GET** `/openApi/api/v3/asset/transferRecord`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| fromAccount | string | Yes | fromAccount, fund：Funding Account spot:Spot Account, stdFutures:Standard Contract, coinMPerp:COIN-M Perpetual Future, USDTMPerp:Perpetual Future |
| toAccount | string | Yes | toAccount, fund:Funding Account spot:Spot Account, stdFutures:Standard Contract, coinMPerp:COIN-M Perpetual Future, USDTMPerp:Perpetual Future |
| tranId | LONG | No | transaction ID, (query by fromAccount|toAccount or transferId) |
| startTime | LONG | No | Starting time1658748648396 |
| endTime | LONG | No | End Time 1658748648396 |
| pageIndex | int64 | No | current page default1 |
| pageSize | int64 | No | Page size default 10 can not exceed 100 |
| recvWindow | LONG | No | Execution window time, cannot be greater than 60000 |
| timestamp | LONG | Yes | current timestamp e.g.1658748648396 |

**Response Body**

| filed | data type | description |
|---|---|---|
| transferId | string | transferId |
| asset | string | Coin Name |
| amount | DECIMAL | Transfer Amount |
| fromAccount | string | fromAccount, fund：Funding Account spot:Spot Account, stdFutures:Standard Contract, coinMPerp:COIN-M Perpetual Future, USDTMPerp:Perpetual Future |
| toAccount | string | toAccount, fund：Funding Account spot:Spot Account, stdFutures:Standard Contract, coinMPerp:COIN-M Perpetual Future, USDTMPerp:Perpetual Future |
| timestamp | LONG | Transfer time stamp |

**Request Example**

```json
{
  "fromAccount": "fund",
  "toAccount": "spot"
}
```

**Response Example**

```json
{
  "total": 2,
  "rows": [
    {
      "asset": "VST",
      "amount": "100000.00000000000000000000",
      "status": "CONFIRMED",
      "transferId": "37600111",
      "timestamp": 1702252271000,
      "fromAccount": "fund",
      "toAccount": "spot"
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/api/v3/asset/transferRecord'
    method = "GET"
    paramsMap = {
    "fromAccount": "fund",
    "toAccount": "spot"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Fund Account Assets

**GET** `/openApi/fund/v1/account/balance`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| asset | string | No | Coin name, return all when not transmitted |
| recvWindow | int64 | No | Timestamp of initiating the request, Unit: milliseconds |
| timestamp | int64 | Yes | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| balances | Array | Asset list, element fields refer to the following table |

**Request Example**

```json
{
  "asset": "USDT",
  "recvWindow": "60000"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "",
  "debugMsg": "",
  "data": {
    "balances": [
      {
        "asset": "USDT",
        "free": "566773.193402631",
        "locked": "244.18616265388994"
      },
      {
        "asset": "CHEEMS",
        "free": "294854132046232",
        "locked": "18350553840"
      },
      {
        "asset": "VST",
        "free": "0",
        "locked": "0"
      }
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/fund/v1/account/balance'
    method = "GET"
    paramsMap = {
    "asset": "USDT",
    "recvWindow": "60000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Main account internal transfer records

**GET** `/openApi/wallets/v1/capital/innerTransfer/records`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| coin | string | Yes | Transfer coin name |
| transferClientId | string | No | Client's self-defined internal transfer ID. When both platform ID and transferClientId are provided as input, the query will be based on the platform ID. |
| startTime | long | No | Start time |
| endTime | long | No | End time |
| offset | int64 | No | Starting record number, default is 0 |
| limit | int64 | No | Page size, default is 100, maximum is 1000 |
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| data | object | Inner transfer records list |
| total | int64 | Total number of addresses |
| id | long | Inner transfer ID |
| coin | string | Coin name |
| receiver | long | Receiver UID |
| amount | decimal | Transfer amount |
| time | long | Internal transfer time |
| status | Integer | Status 4-Pending review 5-Failed 6-Completed |
| transferClientId | string | Client's self-defined internal transfer ID. When both platform ID and transferClientId are provided as input, the query will be based on the platform ID. |
| fromUid | long | Payer's account |
| recordType | string | Out: transfer out record, in: transfer in record |

**Request Example**

```json
{
  "recvWindow": "30000",
  "limit": "1000",
  "coin": "BTC",
  "startTime": "1701519898118",
  "endTime": "1702383898118"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1702383898844,
  "data": {
    "data": [
      {
        "id": 1251111922229444400,
        "coin": "BTC",
        "receiver": 1128763679,
        "amount": 0.0072366,
        "status": 6,
        "fromUid": 1128763678,
        "recordType": "out"
      }
    ],
    "total": 1
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/wallets/v1/capital/innerTransfer/records'
    method = "GET"
    paramsMap = {
    "recvWindow": "30000",
    "limit": "1000",
    "coin": "BTC",
    "startTime": "1701519898118",
    "endTime": "1702383898118"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Asset overview

**GET** `/openApi/account/v1/allAccountBalance`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| accountType | string | No | Account type, if left blank, all assets of the account will be checked by default. spot: spot (fund account), stdFutures: standard futures account, coinMPerp: coin base account, USDTMPerp: U base account, copyTrading: copy trading account, grid: grid account, eran: wealth account, c2c: c2c account. |
| timestamp | int64 | Yes | Request valid time window value, Unit: milliseconds |
| recvWindow | int64 | No | Timestamp of initiating the request, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| accountType | string | Account type, if left blank, all assets of the account will be checked by default. spot: spot (fund account), stdFutures: standard futures account, coinMPerp: coin base account, USDTMPerp: U base account, copyTrading: copy trading account, grid: grid account, eran: wealth account, c2c: c2c account. |
| usdtBalance | string | Equivalent to USDT amount |

**Request Example**

```json
{
  "accountType": "sopt",
  "recvWindow": "6000"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1719494258281,
  "data": {
    "result": [
      {
        "accountType": "sopt",
        "usdtBalance": "100"
      }
    ],
    "pageId": 1,
    "total": 1
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/account/v1/allAccountBalance'
    method = "GET"
    paramsMap = {
    "accountType": "sopt",
    "recvWindow": "6000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Wallet Deposits and Withdrawals

#### Deposit records

**GET** `/openApi/api/v3/capital/deposit/hisrec`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| coin | string | No | coin name |
| status | int64 | No | Status (0-In progress 6-Chain uploaded 1-Completed) |
| startTime | LONG | No | Starting time1658748648396 |
| endTime | LONG | No | End Time 1658748648396 |
| offset | int64 | No | offset default0 |
| limit | int64 | No | Page size default 1000 cannot exceed 1000 |
| txId | LONG | No | transaction id |
| recvWindow | LONG | No | Execution window time, cannot be greater than 60000 |
| timestamp | LONG | Yes | current timestamp 1658748648396 |

**Response Body**

| filed | data type | description |
|---|---|---|
| amount | DECIMAL | Recharge amount |
| coin | string | coin name |
| network | string | recharge network |
| status | int64 | Status (0-In progress 6-Chain uploaded 1-Completed) |
| address | string | recharge address |
| addressTag | string | Remark |
| txId | LONG | transaction id |
| insertTime | LONG | transaction hour |
| transferType | LONG | Transaction Type 0 = Recharge |
| unlockConfirm | LONG | confirm times for unlocking |
| confirmTimes | LONG | Network confirmation times |
| sourceAddress | String | Source address |

**Request Example**

```json
{
  "endTime": "1702622588000",
  "recvWindow": "5000",
  "startTime": "1700894588000"
}
```

**Response Example**

```json
[
  {
    "amount": "49999.00000000000000000000",
    "coin": "USDTTRC20",
    "network": "TRC20",
    "status": 1,
    "address": "TP******B4v",
    "addressTag": "",
    "txId": "60*****1d",
    "insertTime": 1701557778000,
    "unlockConfirm": "2/2",
    "confirmTimes": "2/2"
  }
]
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/api/v3/capital/deposit/hisrec'
    method = "GET"
    paramsMap = {
    "endTime": "1702622588000",
    "recvWindow": "5000",
    "startTime": "1700894588000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Withdraw records

**GET** `/openApi/api/v3/capital/withdraw/history`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| id | string | No | Unique id of the withdrawal record returned by the platform |
| coin | string | No | coin name |
| withdrawOrderId | string | No | Custom ID, if there is none, this field will not be returned,When both the platform ID and withdraw order ID are passed as parameters, the query will be based on the platform ID |
| status | int64 | No | 4-Under Review 5-Failed 6-Completed |
| startTime | LONG | No | Starting time1658748648396 |
| endTime | LONG | No | End Time 1658748648396 |
| offset | int64 | No | offset default0 |
| limit | int64 | No | Page size default 1000 cannot exceed 1000 |
| txId | String | No | Withdrawal transaction id |
| recvWindow | LONG | No | Execution window time, cannot be greater than 60000 |
| timestamp | LONG | Yes | current timestamp e.g.1658748648396 |

**Response Body**

| filed | data type | description |
|---|---|---|
| address | string | address |
| amount | DECIMAL | Withdrawal amount |
| applyTime | Date | withdraw time |
| coin | string | coin name |
| id | string | The id of the withdrawal |
| withdrawOrderId | string | Custom ID, if there is none, this field will not be returned,When both the platform ID and withdraw order ID are passed as parameters, the query will be based on the platform ID |
| network | string | Withdrawal network |
| status | int64 | 4-Under Review 5-Failed 6-Completed |
| transactionFee | string | handling fee |
| confirmNo | int64 | Withdrawal confirmation times |
| info | string | Reason for withdrawal failure |
| txId | String | Withdrawal transaction id |
| sourceAddress | String | Source address |
| transferType | int64 | Transfer type: 1 Withdrawal, 2 Internal transfer |
| addressTag | string | Some currencies like XRP/XMR allow filling in secondary address tags |

**Request Example**

```json
{
  "coin": "USDT",
  "endTime": "1702536564000",
  "recvWindow": "60",
  "startTime": "1702450164000"
}
```

**Response Example**

```json
[
  {
    "address": "TR****zc",
    "amount": "3500.00000000000000000000",
    "applyTime": "2023-12-14T04:05:02.000+08:00",
    "coin": "USDTTRC20",
    "id": "125*****98",
    "network": "TRC20",
    "transferType": 1,
    "transactionFee": "1.00000000000000000000",
    "confirmNo": 2,
    "info": "",
    "txId": "b9***********b67"
  }
]
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/api/v3/capital/withdraw/history'
    method = "GET"
    paramsMap = {
    "coin": "USDT",
    "endTime": "1702536564000",
    "recvWindow": "60",
    "startTime": "1702450164000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query currency deposit and withdrawal data

**GET** `/openApi/wallets/v1/capital/config/getall`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| coin | string | No | Coin identification |
| displayName | string | No | The platform displays the currency pair name for display only. Unlike coins, coins need to be used for withdrawal and recharge. |
| timestamp | int64 | Yes | Timestamp of initiating the request, Unit: milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| coin | string | Coin identification |
| displayName | string | The platform displays the currency pair name for display only. Unlike coins, coins need to be used for withdrawal and recharge. |
| name | string | Coin name |
| networkList | Network | Network information |

**Request Example**

```json
{}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1702623271477,
  "data": [
    {
      "coin": "BTC",
      "name": "BTC",
      "networkList": [
        {
          "name": "BTC",
          "network": "BTC",
          "isDefault": true,
          "minConfirm": 2,
          "withdrawEnable": true,
          "depositEnable": true,
          "withdrawFee": "0.0006",
          "withdrawMax": "1.17522",
          "withdrawMin": "0.0005",
          "depositMin": "0.0002"
        },
        {
          "name": "BTC",
          "network": "BEP20",
          "isDefault": false,
          "minConfirm": 15,
          "withdrawEnable": true,
          "depositEnable": true,
          "withdrawFee": "0.0000066",
          "withdrawMax": "1.17522",
          "withdrawMin": "0.0000066",
          "depositMin": "0.0002"
        }
      ]
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/wallets/v1/capital/config/getall'
    method = "GET"
    paramsMap = {}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Withdraw

**POST** `/openApi/wallets/v1/capital/withdraw/apply`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| coin | string | Yes | Coin name |
| network | string | No | Network name, use default network if not transmitted |
| address | string | Yes | Withdrawal address |
| addressTag | string | No | Tag or memo, some currencies support tag or memo |
| amount | float64 | Yes | Withdrawal amount |
| walletType | int64 | Yes | Account type, 1 Fund Account; 2 Standard Futures Account; 3 Perpetual Futures Account; 4 Spot Account. When the funding account balance is insufficient, the system will automatically replenish funds from the spot account. |
| withdrawOrderId | string | No | Customer-defined withdrawal ID, a combination of numbers and letters, with a length of less than 100 characters |
| vaspEntityId | string | No | Payment platform information, only KYC=KOR (Korean individual users) must pass this field. List values Bithumb, Coinone, Hexlant, Korbit, Upbit, Others, and select Others if there are no corresponding options |
| recipientLastName | string | No | The recipient's surname is in English, and only KYC=KOR (Korean individual users) must pass this field. No need to fill in when vaspAntityId=Others |
| recipientFirstName | string | No | The recipient's name in English, only KYC=KOR (Korean individual users) must pass this field. No need to fill in when vaspAntityId=Others. |
| dateOfbirth | string | No | The payee's date of birth (example 1999-09-09) must be passed as this field only for KYC=KOR (Korean individual users). No need to fill in when vaspAntityId=Others. |
| timestamp | int64 | Yes | Timestamp of initiating the request, Unit: milliseconds |
| recvWindow | int64 | No | Request valid time window value, Unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| id | string | The platform returns the unique ID of the internal transfer record. |
| withdrawOrderId | string | Customer-defined withdrawal ID, a combination of numbers and letters, with a length of less than 100 characters |

**Request Example**

```json
{
  "address": "0x8****11",
  "addressTag": "None",
  "amount": "4998.0",
  "coin": "USDT",
  "network": "BEP20",
  "walletType": "1"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1702619168218,
  "data": {
    "id": "125*****4"
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/wallets/v1/capital/withdraw/apply'
    method = "POST"
    paramsMap = {
    "address": "0x8****11",
    "addressTag": "None",
    "amount": "4998.0",
    "coin": "USDT",
    "network": "BEP20",
    "walletType": "1"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Main Account Deposit Address

**GET** `/openApi/wallets/v1/capital/deposit/address`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| coin | string | Yes | Name of the coin for transfer |
| offset | int64 | No | Starting record number, default is 0 |
| limit | int64 | No | Page size, default is 100, maximum is 1000 |
| timestamp | int64 | Yes | Timestamp of the request in milliseconds |
| recvWindow | int64 | No | Request window validity, in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| data | object | List of deposit addresses |
| total | int64 | Total number of addresses |
| coin | string | Name of the coin |
| network | string | Name of the network |
| address | string | Deposit address |
| addressWithPrefix | string | Deposit address with prefix |
| tag | string | Address tag |
| status | int64 | 0 for activated, 1 for applied, 2 for not applied |
| walletType | int64 | Account type, 1 Fund Account; 2 Standard Futures Account; 3 Perpetual Futures Account; 4 Spot Account |

**Request Example**

```json
{
  "coin": "USDT",
  "limit": "1000",
  "offset": "0",
  "recvWindow": "0"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1702623918163,
  "data": {
    "data": [
      {
        "coinId": 760,
        "coin": "USDT",
        "network": "ERC20",
        "address": "40e*****95",
        "tag": ""
      },
      {
        "coinId": 780,
        "coin": "USDT",
        "network": "TRC20",
        "address": "40e*****95",
        "tag": ""
      },
      {
        "coinId": 799,
        "coin": "USDT",
        "network": "BEP20",
        "address": "40e*****95",
        "tag": ""
      },
      {
        "coinId": 857,
        "coin": "USDT",
        "network": "SOL",
        "address": "40e*****95",
        "tag": ""
      },
      {
        "coinId": 1192,
        "coin": "USDT",
        "network": "POLYGON",
        "address": "40e*****95",
        "tag": ""
      },
      {
        "coinId": 1367,
        "coin": "USDT",
        "network": "ARBITRUM",
        "address": "40e*****95",
        "tag": ""
      },
      {
        "coinId": 1371,
        "coin": "USDT",
        "network": "OPTIMISM",
        "address": "40e*****95",
        "tag": ""
      }
    ],
    "total": 7
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/wallets/v1/capital/deposit/address'
    method = "GET"
    paramsMap = {
    "coin": "USDT",
    "limit": "1000",
    "offset": "0",
    "recvWindow": "0"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Deposit risk control records

**GET** `/openApi/wallets/v1/capital/deposit/riskRecords`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| filed | data type | description |  |

**Request Example**

```json
{}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1706839654997,
  "data": [
    {
      "uid": "",
      "coin": "",
      "amount": "",
      "sourceAddress": "",
      "address": "",
      "insetTime": ""
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/wallets/v1/capital/deposit/riskRecords'
    method = "GET"
    paramsMap = {}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Sub-account Management

#### Create Sub-account

**POST** `/openApi/subAccount/v1/create`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| subAccountString | string | Yes | Sub-account username (must start with a letter, contain numbers, and be more than 6 characters long) |
| note | string | No | Remark |
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | The validity time window of the request in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| subUid | long | Sub-account UID |
| subAccountString | string | Sub-account username |
| note | string | Sub-account remark |

**Request Example**

```json
{
  "recvWindow": 10000,
  "subAccountString": "abc123456"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1702288510557,
  "data": {
    "subUid": "16777654",
    "subAccountString": "abc123456"
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import json
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/subAccount/v1/create'
    method = "POST"
    paramsMap = {
    "recvWindow": 10000,
    "subAccountString": "abc123456"
}
    return send_request(method, path, paramsMap, payload)

def get_sign(api_secret, payload_str):
    signature = hmac.new(api_secret.encode("utf-8"), payload_str.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature

def get_parameters_string(paramsMap, timestamp):
    """Build parameters string for signature calculation"""
    paramsDict = {}
    if paramsMap:
        for key, value in paramsMap.items():
            paramsDict[key] = value
    paramsDict['timestamp'] = timestamp
    
    sorted_keys = sorted(paramsDict.keys())
    params_list = []
    for key in sorted_keys:
        value = paramsDict[key]
        if isinstance(value, (list, dict)):
            value = json.dumps(value, separators=(",", ":"))
        params_list.append("%s=%s" % (key, value))
    return "&".join(params_list)

def send_request(method, path, paramsMap, payload):
    timestamp = str(int(time.time() * 1000))
    
    # Build parameters string for signature
    paramsStr = get_parameters_string(paramsMap, timestamp)
    sign = get_sign(SECRETKEY, paramsStr)
    
    # Build request body with all parameters including timestamp and signature
    bodyParams = {}
    if paramsMap:
        for key, value in paramsMap.items():
            bodyParams[key] = value
    bodyParams['timestamp'] = int(timestamp)
    bodyParams['signature'] = sign
    
    url = "%s%s" % (APIURL, path)
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
        'Content-Type': 'application/json'
    }
    response = requests.request(method, url, headers=headers, json=bodyParams)
    return response.text

if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query API KEY Permissions

**GET** `/openApi/v1/account/apiPermissions`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | The validity time window of the request in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| apiKey | String | apiKey |
| permissions | array | Permissions, 1 - Spot trading, 2 - Read, 3 - Professional contract trading, 4 - Universal transfer, 5 - Withdraw, 7 - Allow intra-sub-account transfer |
| ipAddresses | array | IP whitelist |
| note | String | Remark |

**Request Example**

```json
{}
```

**Response Example**

```json
{
  "apiKey": "",
  "permissions": [
    1,
    2
  ],
  "ipAddresses": [],
  "note": "demo"
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/v1/account/apiPermissions'
    method = "GET"
    paramsMap = {}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Account UID

**GET** `/openApi/account/v1/uid`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | The validity time window of the request in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| uid | long | User UID |

**Request Example**

```json
{}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1702558965648,
  "data": {
    "uid": 16844999
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/account/v1/uid'
    method = "GET"
    paramsMap = {}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Sub-account List

**GET** `/openApi/subAccount/v1/list`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| subUid | long | No | Sub-account UID |
| subAccountString | string | No | Sub-account username |
| isFeeze | bool | No | Is frozen |
| page | int64 | Yes | Page number, starting from 1 |
| limit | int64 | Yes | Page size, max 1000 |
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | Request validity time window in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| subUid | long | Sub-account UID |
| subAccountString | string | Sub-account username |
| note | string | Sub-account remark |
| freeze | bool | Is frozen |
| createTime | long | Creation time |

**Request Example**

```json
{
  "limit": 100
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1701088491202,
  "data": {
    "result": [
      {
        "subUid": "16477999",
        "subAccountString": "abc123456",
        "note": "",
        "freeze": false,
        "createTime": 1700847351000
      }
    ],
    "pageId": 1,
    "total": 1
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/subAccount/v1/list'
    method = "GET"
    paramsMap = {
    "limit": 100
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Sub-account Asset Account

**GET** `/openApi/subAccount/v1/assets`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| subUid | long | Yes | Sub-account UID |
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | Request validity time window in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| asset | string | Asset name |
| free | double | Available balance |
| locked | double | Locked asset |

**Request Example**

```json
{
  "subUid": "16477999"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1701077668349,
  "data": {
    "balances": [
      {
        "asset": "ETH",
        "free": 0.0068,
        "locked": 0
      }
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/subAccount/v1/assets'
    method = "GET"
    paramsMap = {
    "subUid": "16477999"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Create Sub-account API Key

**POST** `/openApi/subAccount/v1/apiKey/create`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| subUid | long | Yes | Sub-account UID |
| note | string | Yes | Note |
| permissions | Array | Yes | Permissions, 1 - Spot trading, 2 - Read, 3 - Professional contract trading, 4 - Universal transfer, 5 - Withdraw, 7 - Allow intra-sub-account transfer |
| ipAddresses | Array | No | IP Whitelist |
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | Request validity time window in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| apiKey | string |  |
| apiSecret | string | API Secret |
| permissions | Array | Permissions, 1 - Spot trading, 2 - Read, 3 - Professional contract trading, 4 - Universal transfer, 5 - Withdraw, 7 - Allow intra-sub-account transfer |
| ipAddresses | Array | IP Whitelist |
| note | string | Note |

**Request Example**

```json
{
  "subUid": 14189999,
  "note": "abc6798",
  "permissions": [
    3
  ],
  "ipAddresses": [
    "8.222.71.59"
  ]
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1701526872165,
  "data": {
    "note": "abc6798",
    "apiKey": "kRaent****jg",
    "apiSecret": "2b****Og",
    "permissions": [],
    "ipAddresses": []
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import json
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/subAccount/v1/apiKey/create'
    method = "POST"
    paramsMap = {
    "subUid": 14189999,
    "note": "abc6798",
    "permissions": [
        3
    ],
    "ipAddresses": [
        "8.222.71.59"
    ]
}
    return send_request(method, path, paramsMap, payload)

def get_sign(api_secret, payload_str):
    signature = hmac.new(api_secret.encode("utf-8"), payload_str.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature

def get_parameters_string(paramsMap, timestamp):
    """Build parameters string for signature calculation"""
    paramsDict = {}
    if paramsMap:
        for key, value in paramsMap.items():
            paramsDict[key] = value
    paramsDict['timestamp'] = timestamp
    
    sorted_keys = sorted(paramsDict.keys())
    params_list = []
    for key in sorted_keys:
        value = paramsDict[key]
        if isinstance(value, (list, dict)):
            value = json.dumps(value, separators=(",", ":"))
        params_list.append("%s=%s" % (key, value))
    return "&".join(params_list)

def send_request(method, path, paramsMap, payload):
    timestamp = str(int(time.time() * 1000))
    
    # Build parameters string for signature
    paramsStr = get_parameters_string(paramsMap, timestamp)
    sign = get_sign(SECRETKEY, paramsStr)
    
    # Build request body with all parameters including timestamp and signature
    bodyParams = {}
    if paramsMap:
        for key, value in paramsMap.items():
            bodyParams[key] = value
    bodyParams['timestamp'] = int(timestamp)
    bodyParams['signature'] = sign
    
    url = "%s%s" % (APIURL, path)
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
        'Content-Type': 'application/json'
    }
    response = requests.request(method, url, headers=headers, json=bodyParams)
    return response.text

if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query API Key Information

**GET** `/openApi/account/v1/apiKey/query`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| uid | long | Yes | User UID |
| apiKey | string | No |  |
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | Request validity time window in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| apiKey | string |  |
| note | string | Note |
| permissions | Array | Permissions, 1 - Spot trading, 2 - Read, 3 - Professional contract trading, 4 - Universal transfer, 5 - Withdraw |
| ipAddresses | Array | IP Whitelist |
| createTime | long | Creation time |
| updateTime | long | Update time |

**Request Example**

```json
{
  "uid": 16789999
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1702351994615,
  "data": {
    "apiInfos": [
      {
        "apiKey": "zF*******zQ",
        "note": "note****",
        "permissions": [
          1,
          2,
          3,
          4,
          7
        ],
        "ipAddresses": [
          ""
        ],
        "status": 0,
        "createTime": 1702289687211,
        "updateTime": 1702289687000
      }
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/account/v1/apiKey/query'
    method = "GET"
    paramsMap = {
    "uid": 16789999
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Edit Sub-Account API Key

**POST** `/openApi/subAccount/v1/apiKey/edit`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| subUid | long | Yes | Sub-account UID |
| apiKey | string | Yes |  |
| note | string | Yes | Note |
| permissions | Array | Yes | Permissions, 1 - Spot trading, 2 - Read, 3 - Professional contract trading, 4 - Universal transfer, 7 - Allow sub-account internal transfer |
| ipAddresses | Array | No | IP Whitelist |
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | Request validity time window in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| permissions | Array | Permissions, 1 - Spot trading, 2 - Read, 3 - Professional contract trading, 4 - Universal transfer, 7 - Allow sub-account internal transfer |
| ipAddresses | Array | IP Whitelist |
| note | string | Note |

**Request Example**

```json
{
  "subUid": "16259999",
  "apiKey": "CK***g",
  "ipAddresses": [
    "51.**.**.172",
    "51.**.**.135"
  ],
  "note": "note",
  "permissions": [
    1,
    2,
    3,
    4,
    6,
    7
  ]
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1699785925994,
  "data": {
    "note": "note",
    "permissions": [
      1,
      2,
      3,
      4,
      6,
      7
    ],
    "ipAddresses": [
      "51.**.**.172",
      "51.**.**.135"
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import json
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/subAccount/v1/apiKey/edit'
    method = "POST"
    paramsMap = {
    "subUid": "16259999",
    "apiKey": "CK***g",
    "ipAddresses": [
        "51.**.**.172",
        "51.**.**.135"
    ],
    "note": "note",
    "permissions": [
        1,
        2,
        3,
        4,
        6,
        7
    ]
}
    return send_request(method, path, paramsMap, payload)

def get_sign(api_secret, payload_str):
    signature = hmac.new(api_secret.encode("utf-8"), payload_str.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature

def get_parameters_string(paramsMap, timestamp):
    """Build parameters string for signature calculation"""
    paramsDict = {}
    if paramsMap:
        for key, value in paramsMap.items():
            paramsDict[key] = value
    paramsDict['timestamp'] = timestamp
    
    sorted_keys = sorted(paramsDict.keys())
    params_list = []
    for key in sorted_keys:
        value = paramsDict[key]
        if isinstance(value, (list, dict)):
            value = json.dumps(value, separators=(",", ":"))
        params_list.append("%s=%s" % (key, value))
    return "&".join(params_list)

def send_request(method, path, paramsMap, payload):
    timestamp = str(int(time.time() * 1000))
    
    # Build parameters string for signature
    paramsStr = get_parameters_string(paramsMap, timestamp)
    sign = get_sign(SECRETKEY, paramsStr)
    
    # Build request body with all parameters including timestamp and signature
    bodyParams = {}
    if paramsMap:
        for key, value in paramsMap.items():
            bodyParams[key] = value
    bodyParams['timestamp'] = int(timestamp)
    bodyParams['signature'] = sign
    
    url = "%s%s" % (APIURL, path)
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
        'Content-Type': 'application/json'
    }
    response = requests.request(method, url, headers=headers, json=bodyParams)
    return response.text

if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Delete Sub-Account API Key

**POST** `/openApi/subAccount/v1/apiKey/del`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| subUid | long | Yes | Sub-account UID |
| apiKey | string | Yes |  |
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | Request validity time window in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | error msg |  |

**Request Example**

```json
{
  "subUid": 14189999,
  "apiKey": "2W****mA"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1702021810315
}
```

**Python Demo**

```python
import time
import requests
import hmac
import json
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/subAccount/v1/apiKey/del'
    method = "POST"
    paramsMap = {
    "subUid": 14189999,
    "apiKey": "2W****mA"
}
    return send_request(method, path, paramsMap, payload)

def get_sign(api_secret, payload_str):
    signature = hmac.new(api_secret.encode("utf-8"), payload_str.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature

def get_parameters_string(paramsMap, timestamp):
    """Build parameters string for signature calculation"""
    paramsDict = {}
    if paramsMap:
        for key, value in paramsMap.items():
            paramsDict[key] = value
    paramsDict['timestamp'] = timestamp
    
    sorted_keys = sorted(paramsDict.keys())
    params_list = []
    for key in sorted_keys:
        value = paramsDict[key]
        if isinstance(value, (list, dict)):
            value = json.dumps(value, separators=(",", ":"))
        params_list.append("%s=%s" % (key, value))
    return "&".join(params_list)

def send_request(method, path, paramsMap, payload):
    timestamp = str(int(time.time() * 1000))
    
    # Build parameters string for signature
    paramsStr = get_parameters_string(paramsMap, timestamp)
    sign = get_sign(SECRETKEY, paramsStr)
    
    # Build request body with all parameters including timestamp and signature
    bodyParams = {}
    if paramsMap:
        for key, value in paramsMap.items():
            bodyParams[key] = value
    bodyParams['timestamp'] = int(timestamp)
    bodyParams['signature'] = sign
    
    url = "%s%s" % (APIURL, path)
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
        'Content-Type': 'application/json'
    }
    response = requests.request(method, url, headers=headers, json=bodyParams)
    return response.text

if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Freeze/Unfreeze Sub-Account

**POST** `/openApi/subAccount/v1/updateStatus`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| subUid | long | Yes | Sub-account UID |
| freeze | bool | Yes | Whether to freeze the account |
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | Request validity time window in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| subUid | long | Sub-account UID |
| freeze | bool | Whether it is frozen |

**Request Example**

```json
{}
```

**Python Demo**

```python
import time
import requests
import hmac
import json
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/subAccount/v1/updateStatus'
    method = "POST"
    paramsMap = {}
    return send_request(method, path, paramsMap, payload)

def get_sign(api_secret, payload_str):
    signature = hmac.new(api_secret.encode("utf-8"), payload_str.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature

def get_parameters_string(paramsMap, timestamp):
    """Build parameters string for signature calculation"""
    paramsDict = {}
    if paramsMap:
        for key, value in paramsMap.items():
            paramsDict[key] = value
    paramsDict['timestamp'] = timestamp
    
    sorted_keys = sorted(paramsDict.keys())
    params_list = []
    for key in sorted_keys:
        value = paramsDict[key]
        if isinstance(value, (list, dict)):
            value = json.dumps(value, separators=(",", ":"))
        params_list.append("%s=%s" % (key, value))
    return "&".join(params_list)

def send_request(method, path, paramsMap, payload):
    timestamp = str(int(time.time() * 1000))
    
    # Build parameters string for signature
    paramsStr = get_parameters_string(paramsMap, timestamp)
    sign = get_sign(SECRETKEY, paramsStr)
    
    # Build request body with all parameters including timestamp and signature
    bodyParams = {}
    if paramsMap:
        for key, value in paramsMap.items():
            bodyParams[key] = value
    bodyParams['timestamp'] = int(timestamp)
    bodyParams['signature'] = sign
    
    url = "%s%s" % (APIURL, path)
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
        'Content-Type': 'application/json'
    }
    response = requests.request(method, url, headers=headers, json=bodyParams)
    return response.text

if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Authorize Sub-Account Internal Transfer

**POST** `/openApi/account/v1/innerTransfer/authorizeSubAccount`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| subUids | string | Yes | Comma-separated list of user UIDs |
| transferable | boolean | Yes | Whether allowed, true for allowed, false for denied |
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | Request validity time window in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| code | error msg |  |

**Request Example**

```json
{
  "subUids": "16789999",
  "transferable": "true"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1702520269455,
  "data": true
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/account/v1/innerTransfer/authorizeSubAccount'
    method = "POST"
    paramsMap = {
    "subUids": "16789999",
    "transferable": "true"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Sub-account Internal Transfer

**POST** `/openApi/wallets/v1/capital/subAccountInnerTransfer/apply`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| coin | string | Yes | Name of the transfer currency |
| userAccountType | int64 | Yes | User account type: 1 = UID, 2 = Phone number, 3 = Email |
| userAccount | string | Yes | User account: UID, phone number, or email |
| amount | float64 | Yes | Transfer amount |
| callingCode | string | No | Phone area code. Required when userAccountType = 2 |
| walletType | int64 | Yes | Account type: 1 = Fund Account; 2 = Standard Futures Account; 3 = Perpetual Futures Account; 15 = Spot Account |
| transferClientId | string | No | Client-defined internal transfer ID. Must be alphanumeric and less than 100 characters |
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | Request validity time window, in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| id | string | Unique ID of the internal transfer record returned by the platform |

**Request Example**

```json
{
  "amount": 20,
  "coin": "usdt",
  "userAccount": "16689999",
  "userAccountType": 1,
  "walletType": 1
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1702520425652,
  "data": {
    "id": "12*******12"
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/wallets/v1/capital/subAccountInnerTransfer/apply'
    method = "POST"
    paramsMap = {
    "amount": 20,
    "coin": "usdt",
    "userAccount": "16689999",
    "userAccountType": 1,
    "walletType": 1
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Main Accoun internal transfer

**POST** `/openApi/wallets/v1/capital/innerTransfer/apply`

- **Rate Limit**: UID Rate Limit 2/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| coin | string | Yes | Name of the transferred currency |
| userAccountType | int64 | Yes | User account type 1=UID 2=phone number 3=email |
| userAccount | string | Yes | User account: UID, phone number, email |
| amount | float64 | Yes | Transfer amount |
| callingCode | string | No | Area code for telephone, required when userAccountType=2. |
| walletType | int64 | Yes | Account type, 1 Fund Account; 2 Standard Futures Account; 3 Perpetual Futures Account; 4 Spot Account |
| transferClientId | string | No | Custom ID for internal transfer by the client, combination of numbers and letters, length less than 100 characters |
| timestamp | int64 | Yes | The timestamp of the request, in milliseconds. |
| recvWindow | int64 | No | Request validity time window, unit: milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| id | string | The platform returns the unique ID of the internal transfer record. |
| transferClientId | string | Custom ID for internal transfer by the client, combination of numbers and letters, length less than 100 characters |

**Request Example**

```json
{
  "amount": "10.0",
  "coin": "USDT",
  "userAccount": "16779999",
  "userAccountType": "1",
  "walletType": "1"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1702558152381,
  "data": {
    "id": "12******1"
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/wallets/v1/capital/innerTransfer/apply'
    method = "POST"
    paramsMap = {
    "amount": "10.0",
    "coin": "USDT",
    "userAccount": "16779999",
    "userAccountType": "1",
    "walletType": "1"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Sub-account Deposit Address

**GET** `/openApi/wallets/v1/capital/subAccount/deposit/address`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| coin | string | Yes | Coin Name |
| subUid | long | Yes | Sub-account UID |
| offset | int64 | No | Offset, defaults to 0 |
| limit | int64 | No | Page size, defaults to 100, max 1000 |
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | Request window validity in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| data | object | Deposit address list |
| total | int64 | Total number of addresses |
| coin | string | Coin Name |
| network | string | Network Name |
| address | string | Deposit Address |
| addressWithPrefix | string | Deposit address with prefix |
| tag | string | Address Tag |
| status | int64 | 0 Active, 1 Pending, 2 Not Applied |
| walletType | int64 | Account type, 1 Fund Account; 2 Standard Futures Account; 3 Perpetual Futures Account; 4 Spot Account |

**Request Example**

```json
{
  "coin": "USDT",
  "limit": "100",
  "offset": 0,
  "subUid": 16239999
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1700741585439,
  "data": {
    "data": [],
    "total": 0
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/wallets/v1/capital/subAccount/deposit/address'
    method = "GET"
    paramsMap = {
    "coin": "USDT",
    "limit": "100",
    "offset": 0,
    "subUid": 16239999
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Sub-account Deposit Address

**GET** `/openApi/wallets/v1/capital/subAccount/deposit/address`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| coin | string | Yes | Coin Name |
| subUid | long | Yes | Sub-account UID |
| offset | int64 | No | Offset, defaults to 0 |
| limit | int64 | No | Page size, defaults to 100, max 1000 |
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | Request window validity in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| data | object | Deposit address list |
| total | int64 | Total number of addresses |
| coin | string | Coin Name |
| network | string | Network Name |
| address | string | Deposit Address |
| addressWithPrefix | string | Deposit address with prefix |
| tag | string | Address Tag |
| status | int64 | 0 Active, 1 Pending, 2 Not Applied |
| walletType | int64 | Account type, 1 Fund Account; 2 Standard Futures Account; 3 Perpetual Futures Account; 4 Spot Account |

**Request Example**

```json
{
  "coin": "USDT",
  "limit": "100",
  "offset": 0,
  "subUid": 16239999
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1700741585439,
  "data": {
    "data": [],
    "total": 0
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/wallets/v1/capital/subAccount/deposit/address'
    method = "GET"
    paramsMap = {
    "coin": "USDT",
    "limit": "100",
    "offset": 0,
    "subUid": 16239999
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Get Sub-account Deposit Records

**GET** `/openApi/wallets/v1/capital/deposit/subHisrec`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| coin | string | No | Transfer currency name |
| subUid | long | No | Sub-account UID, if not filled, query deposit records of all sub-accounts |
| status | int64 | No | Status (0-In progress, 6-Chain uploaded, 1-Completed) |
| startTime | long | No | Start time |
| endTime | long | No | End time |
| offset | int64 | No | Starting record number, default is 0 |
| limit | int64 | No | Page size, default is 100, max 1000 |
| txId | string |  |  |
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| data | object | Internal transfer record list |
| total | int64 | Total number of addresses |
| subUid | long | Sub-account UID |
| amount | decimal | Transfer amount |
| coin | string | Currency name |
| network | string | Network name |
| status | int64 | Status (0-In progress, 6-Chain uploaded, 1-Completed) |
| address | string | Deposit address |
| txId | string | Transaction ID |

**Request Example**

```json
{
  "subUid": "16789999",
  "recvWindow": "10000"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1702436064748,
  "data": {
    "total": 0,
    "data": []
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/wallets/v1/capital/deposit/subHisrec'
    method = "GET"
    paramsMap = {
    "subUid": "16789999",
    "recvWindow": "10000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Sub-account Internal Transfer Records

**GET** `/openApi/wallets/v1/capital/subAccount/innerTransfer/records`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| coin | string | Yes | Coin Name |
| transferClientId | string | No | Custom internal transfer ID. When both platform ID and transferClientId are provided, platform ID will be prioritized. |
| startTime | long | No | Start Time |
| endTime | long | No | End Time |
| offset | int64 | No | Offset, defaults to 0 |
| limit | int64 | No | Page size, defaults to 100, max 1000 |
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | Request window validity in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| data | object | Internal transfer records list |
| total | int64 | Total number of records |
| id | long | Internal transfer ID |
| coin | string | Coin Name |
| receiver | long | Receiver UID |
| amount | decimal | Transfer Amount |
| time | long | Internal transfer time |
| status | Integer | Status 4-Under Review, 5-Failed, 6-Completed |
| transferClientId | string | Custom internal transfer ID |
| fromUid | long | Payer's Account |
| recordType | string | out: Transfer out record, in: Transfer in record |

**Request Example**

```json
{
  "coin": "USDT",
  "startTime": 1694761643000,
  "endTime": 1694765243428,
  "offset": 0,
  "limit": 100,
  "timestamp": 0,
  "recvWindow": 0
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/wallets/v1/capital/subAccount/innerTransfer/records'
    method = "GET"
    paramsMap = {
    "coin": "USDT",
    "startTime": 1694761643000,
    "endTime": 1694765243428,
    "offset": 0,
    "limit": 100,
    "timestamp": 0,
    "recvWindow": 0
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Sub-Mother Account Transfer History

**GET** `/openApi/account/transfer/v1/subAccount/asset/transferHistory`

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| uid | LONG | Yes | UID to query |
| type | ENUM | No | Transfer Type |
| tranId | STRING | No | Transfer ID |
| startTime | LONG | No | Start Time 1658748648396 |
| endTime | LONG | No | End Time 1658748648396 |
| pageId | int64 | No | Current Page Default is 1 |
| pagingSize | int64 | No | Page Size Default is 10, cannot exceed 100 |
| recvWindow | LONG | No | Execution window time, cannot exceed 60000 |
| timestamp | LONG | Yes | Current timestamp, e.g., 1658748648396 |

**Response Body**

| filed | data type | description |
|---|---|---|
| total | LONG | Total |
| rows | Array | Data Array |
| asset | string | Asset Name |
| amount | DECIMAL | Amount |
| type | ENUM | Transfer Type |
| status | string | CONFIRMED |
| tranId | LONG | Transfer ID |
| timestamp | LONG | Transfer Timestamp |
| fromUid | LONG | Payer UID |
| toUid | LONG | Receiver UID |

**Request Example**

```json
{
  "uid": "213342",
  "tranId": "1051323896482406240336",
  "type": "MAIN_CAPITAL_TO_SUB_CAPITAL",
  "startTime": "1719496046943",
  "endTime": "1719596046943",
  "pageId": 1,
  "pagingSize": 10
}
```

**Response Example**

```json
{
  "total": 1,
  "rows": [
    {
      "asset": "VST",
      "amount": "100000.00000000000000000000",
      "type": "MAIN_CAPITAL_TO_SUB_CAPITAL",
      "status": "CONFIRMED",
      "tranId": "1051323896482406240336",
      "timestamp": 1702252271000,
      "fromUid": 2332424,
      "toUid": 123244
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/account/transfer/v1/subAccount/asset/transferHistory'
    method = "GET"
    paramsMap = {
    "uid": "213342",
    "tranId": "1051323896482406240336",
    "type": "MAIN_CAPITAL_TO_SUB_CAPITAL",
    "startTime": "1719496046943",
    "endTime": "1719596046943",
    "pageId": 1,
    "pagingSize": 10
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Sub-Mother Account Transferable Amount

**POST** `/openApi/account/transfer/v1/subAccount/transferAsset/supportCoins`

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| fromUid | LONG | Yes | Payer UID |
| fromAccountType | LONG | Yes | Payer Account Type: 1-Funding Account; 2-Standard Futures Account; 3-Perpetual U-Based Account |
| toUid | LONG | Yes | Receiver UID |
| toAccountType | LONG | Yes | Receiver Account Type: 1-Funding Account; 2-Standard Futures Account; 3-Perpetual U-Based Account |
| recvWindow | LONG | No | Execution window time, cannot exceed 60000 |
| timestamp | LONG | Yes | Current timestamp, e.g., 1658748648396 |

**Response Body**

| filed | data type | description |
|---|---|---|
| coins | ARRAY | List of Supported Coins |
| id | LONG | Coin ID |
| name | STRING | Coin Name (e.g., USDT) |
| availableAmount | DECIMAL | Transferable Amount |

**Request Example**

```json
{
  "recvWindow": "6000",
  "fromUid": "25472377",
  "fromAccountType": "2",
  "toUid": "25316652",
  "toAccountType": "1"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1719498078761,
  "data": {
    "coins": [
      {
        "id": 4,
        "name": "USDT",
        "showName": "Tether",
        "icon": {
          "id": 4,
          "uri": "https://static-app.teststar.cc/icon/USDT.png"
        },
        "type": 0,
        "fiatSymbol": "$",
        "availableAmount": "79.02345678",
        "usdtRate": "1"
      }
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import json
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/account/transfer/v1/subAccount/transferAsset/supportCoins'
    method = "POST"
    paramsMap = {
    "recvWindow": "6000",
    "fromUid": "25472377",
    "fromAccountType": "2",
    "toUid": "25316652",
    "toAccountType": "1"
}
    return send_request(method, path, paramsMap, payload)

def get_sign(api_secret, payload_str):
    signature = hmac.new(api_secret.encode("utf-8"), payload_str.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature

def get_parameters_string(paramsMap, timestamp):
    """Build parameters string for signature calculation"""
    paramsDict = {}
    if paramsMap:
        for key, value in paramsMap.items():
            paramsDict[key] = value
    paramsDict['timestamp'] = timestamp
    
    sorted_keys = sorted(paramsDict.keys())
    params_list = []
    for key in sorted_keys:
        value = paramsDict[key]
        if isinstance(value, (list, dict)):
            value = json.dumps(value, separators=(",", ":"))
        params_list.append("%s=%s" % (key, value))
    return "&".join(params_list)

def send_request(method, path, paramsMap, payload):
    timestamp = str(int(time.time() * 1000))
    
    # Build parameters string for signature
    paramsStr = get_parameters_string(paramsMap, timestamp)
    sign = get_sign(SECRETKEY, paramsStr)
    
    # Build request body with all parameters including timestamp and signature
    bodyParams = {}
    if paramsMap:
        for key, value in paramsMap.items():
            bodyParams[key] = value
    bodyParams['timestamp'] = int(timestamp)
    bodyParams['signature'] = sign
    
    url = "%s%s" % (APIURL, path)
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
        'Content-Type': 'application/json'
    }
    response = requests.request(method, url, headers=headers, json=bodyParams)
    return response.text

if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Sub-Mother Account Asset Transfer Interface

**POST** `/openApi/account/transfer/v1/subAccount/transferAsset`

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| assetName | string | Yes | Asset name, e.g., USDT |
| transferAmount | DECIMAL | Yes | Transfer amount |
| fromUid | LONG | Yes | Payer UID |
| fromType | LONG | Yes | Payer sub-account type: 1-Parent account; 2-Sub-account |
| fromAccountType | LONG | Yes | Payer account type: 1-Funding account; 2-Standard futures account; 3-Perpetual U-based account; 15-Spot account |
| toUid | LONG | Yes | Receiver UID |
| toType | LONG | Yes | Receiver sub-account type: 1-Parent account; 2-Sub-account |
| toAccountType | LONG | Yes | Receiver account type: 1-Funding account; 2-Standard futures account; 3-Perpetual U-based account; 15-Spot account |
| remark | string | Yes | Transfer remarks |
| recvWindow | LONG | No | Execution window time, cannot exceed 60000 |
| timestamp | LONG | Yes | Current timestamp, e.g., 1658748648396 |

**Response Body**

| filed | data type | description |
|---|---|---|
| tranId | STRING | Transfer record ID |

**Request Example**

```json
{
  "recvWindow": "6000",
  "assetName": "USDT",
  "transferAmount": "1.1",
  "fromUid": "25472377",
  "fromAccountType": "2",
  "fromType": "2",
  "toUid": "25316652",
  "toAccountType": "1",
  "toType": "1"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1719494258281,
  "data": {
    "code": 0,
    "timestamp": 1719495091669,
    "data": {
      "tranId": "1051323892566796963873"
    }
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import json
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/account/transfer/v1/subAccount/transferAsset'
    method = "POST"
    paramsMap = {
    "recvWindow": "6000",
    "assetName": "USDT",
    "transferAmount": "1.1",
    "fromUid": "25472377",
    "fromAccountType": "2",
    "fromType": "2",
    "toUid": "25316652",
    "toAccountType": "1",
    "toType": "1"
}
    return send_request(method, path, paramsMap, payload)

def get_sign(api_secret, payload_str):
    signature = hmac.new(api_secret.encode("utf-8"), payload_str.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature

def get_parameters_string(paramsMap, timestamp):
    """Build parameters string for signature calculation"""
    paramsDict = {}
    if paramsMap:
        for key, value in paramsMap.items():
            paramsDict[key] = value
    paramsDict['timestamp'] = timestamp
    
    sorted_keys = sorted(paramsDict.keys())
    params_list = []
    for key in sorted_keys:
        value = paramsDict[key]
        if isinstance(value, (list, dict)):
            value = json.dumps(value, separators=(",", ":"))
        params_list.append("%s=%s" % (key, value))
    return "&".join(params_list)

def send_request(method, path, paramsMap, payload):
    timestamp = str(int(time.time() * 1000))
    
    # Build parameters string for signature
    paramsStr = get_parameters_string(paramsMap, timestamp)
    sign = get_sign(SECRETKEY, paramsStr)
    
    # Build request body with all parameters including timestamp and signature
    bodyParams = {}
    if paramsMap:
        for key, value in paramsMap.items():
            bodyParams[key] = value
    bodyParams['timestamp'] = int(timestamp)
    bodyParams['signature'] = sign
    
    url = "%s%s" % (APIURL, path)
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
        'Content-Type': 'application/json'
    }
    response = requests.request(method, url, headers=headers, json=bodyParams)
    return response.text

if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Batch Query Sub-Account Asset Overview

**GET** `/openApi/subAccount/v1/allAccountBalance`

- **Rate Limit**: UID Rate Limit 5/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| subUid | long | No | Sub-account UID |
| accountType | string | No | Account type, if not filled defaults to all account assets. sopt: Spot (funding account), stdFutures: Standard contract account, coinMPerp: Coin-based account, USDTMPerp: U-based account, copyTrading: Copy trading account, grid: Strategy account, eran: Wealth management account, c2c: C2C account, etc. |
| pageIndex | int64 | Yes | Page index, must be greater than 0 |
| pageSize | int64 | Yes | Page size, must be greater than 0, max 10 |
| timestamp | int64 | Yes | Request timestamp in milliseconds |
| recvWindow | int64 | No | Request valid time window, in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| subUid | long | Sub-account UID |
| accountType | string | Account type, if not filled defaults to all account assets. sopt: Spot (funding account), stdFutures: Standard contract account, coinMPerp: Coin-based account, USDTMPerp: U-based account, copyTrading: Copy trading account, grid: Strategy account, eran: Wealth management account, c2c: C2C account, etc. |
| usdtBalance | string | USDT equivalent amount |

**Request Example**

```json
{
  "subUid": 25316652,
  "accountType": "sopt",
  "pageIndex": 1,
  "pageSize": 10,
  "recvWindow": "6000"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1719494258281,
  "data": {
    "result": [
      {
        "subUid": "16477999",
        "accountBalances": [
          {
            "accountType": "sopt",
            "usdtBalance": "100"
          }
        ]
      }
    ],
    "pageId": 1,
    "total": 1
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/subAccount/v1/allAccountBalance'
    method = "GET"
    paramsMap = {
    "subUid": 25316652,
    "accountType": "sopt",
    "pageIndex": 1,
    "pageSize": 10,
    "recvWindow": "6000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

### Agent

#### Query Invited Users

**GET** `/openApi/agent/v1/account/inviteAccountList`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| startTime | int64 | No | Start timestamp （millisecond）, The maximum query window is 30 days. If you want to retrieve all data, you can leave the startTime and endTime fields blank. |
| endTime | int64 | No | end timestamp (millisecond), The maximum query window is 30 days. If querying for all data, startTime and endTime can be left blank |
| lastUid | int64 | No | User UID, must be transmitted when the queried data exceeds 10,000.The first request does not need to be passed, and the last uid of the current page is passed each time afterwards |
| pageIndex | int64 | Yes | Page number for pagination, must be greater than 0 |
| pageSize | int64 | Yes | The number of pages must be greater than 0 and the maximum value is 200 |
| recvWindow | int64 | Yes | Request valid time window, in milliseconds. Default is 5 seconds if not provided. |
| timestamp | int64 | No | Request timestamp in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| uid | string | Invited User UID |
| ownInviteCode | string | Invitation code for Invited User |
| inviterSid | long | superiors Uid |
| InvitationCode | string | Invitation code for superiors |
| registerTime | long | Registration timestamp, unit: milliseconds |
| directInvitation | boolean | true: Direct invitation, false: Indirect invitation |
| kycResult | string | true : KYC,false:no KYC |
| deposit | boolean | true (Deposited), false (Not deposited) |
| balanceVolume | string | net assets(USDT) |
| trade | boolean | true: Traded, false: Not traded, excluding trades made with trial funds or additional funds |
| userLevel | int64 | Customer level |
| commissionRatio | int64 | Commission percentage, unit: % |
| currentBenefit | int64 | Current welfare method: 0 - No welfare, 1 - Fee cashback, 2 - Perpetual fee discount |
| benefitRatio | int64 | Transaction fee reduction percentage, unit: % |
| benefitExpiration | long | Welfare expiration timestamp, unit: milliseconds |

**Request Example**

```json
{
  "pageIndex": "1",
  "pageSize": "2"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1690428366803,
  "data": {
    "list": [
      {
        "uid": 24828902,
        "ownInviteCode": "LYA1453",
        "superiorsUid": 2293934,
        "InvitationCode": "LYA2023",
        "registerDateTime": 1688992720000,
        "directInvitation": false,
        "kycResult": "false",
        "deposit": false,
        "trade": false,
        "userLevel": 0,
        "commissionRatio": 3,
        "currentBenefit": 0,
        "benefitRatio": 0,
        "benefitExpiration": 0
      }
    ],
    "total": 1,
    "currentAgentUid": 1115195195666423800
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/agent/v1/account/inviteAccountList'
    method = "GET"
    paramsMap = {
    "pageIndex": "1",
    "pageSize": "2"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Daily commission details

**GET** `/openApi/agent/v2/reward/commissionDataList`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| uid | long | No | Inquire about the daily commission of the user who invited the invitation by their UID. |
| invitationCode | string | No | Invitation code: Check the daily commissions of users associated with that invitation code. |
| businessType | string | No | perpetualFutures: Perpetual contracts; standardFutures: Standard contracts; spot: Spot trading; copyTradePro: External copy trading; if empty, it defaults to querying all. |
| startTime | date | Yes | Start timestamp, unit: days, maximum query window size is 7 days, window panning range is the most recent 366 days. |
| endTime | date | Yes | End timestamp, unit: days; maximum query window size: 7 days; window scrolling range: the most recent 366 days. |
| pageIndex | int64 | Yes | Page number for pagination, must be greater than 0 |
| pageSize | int64 | Yes | Page size for pagination, must be greater than 0 with a maximum value of 100. |
| recvWindow | int64 | Yes | Request the valid time window value, in milliseconds. |
| timestamp | int64 | No | Request timestamp in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| uid | long | Invite User UID |
| commissionTime | long | Rebate timestamp, unit: day |
| tradingVolume | string | Transaction volume (USDT) |
| commission | string | your commission |
| expectedTradingFees | string | Platform account receivable fees |
| offsetTradingFees | string | Fee deduction amount |
| collectedTradingFees | string | Platform's Actual Transaction Fee |
| rebateRatio | string | Cash back ratio |
| tradingRebate | string | User transaction rebate |

**Request Example**

```json
{
  "uid": 24391361,
  "invitationCode": "LYA2025",
  "businessType": "",
  "pageIndex": "1",
  "pageSize": "2",
  "startTime": "1688992720000",
  "endTime": "1689426920000"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1690428196386,
  "data": {
    "list": [
      {
        "uid": 24391361,
        "commissionTime": 1689350400000,
        "tradingVolume": "6660.05",
        "commission": "2.37932209",
        "expectedTradingFees ": "6660.05",
        "offsetTradingFees": "2.37932209",
        "collectedTradingFees": "6660.05",
        "rebateRatio": "0.2",
        "tradingRebate": "6660.05"
      }
    ],
    "total": 43,
    "currentAgentUid": 1115195195666423800
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/agent/v2/reward/commissionDataList'
    method = "GET"
    paramsMap = {
    "uid": 24391361,
    "invitationCode": "LYA2025",
    "businessType": "",
    "pageIndex": "1",
    "pageSize": "2",
    "startTime": "1688992720000",
    "endTime": "1689426920000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query agent user information

**GET** `/openApi/agent/v1/account/inviteRelationCheck`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| uid | long | Yes | Invited User UID |

**Response Body**

| filed | data type | description |
|---|---|---|
| uid | long | Invited User UID |
| existInviter | string | true :There is an inviter ,false:There is no inviter |
| inviteResult | boolean | true: invitation relationship,false: non-invitation relationship |
| directInvitation | boolean | true: Direct invitation, false: Indirect invitation |
| inviterSid | long | superiors Uid |
| registerTime | long | Registration timestamp, unit: milliseconds |
| deposit | boolean | true :Deposited, false :Not deposited |
| kycResult | string | true : KYC,false:no KYC |
| balanceVolume | string | net assets(USDT) |
| trade | boolean | true: Traded, false: Not traded, excluding trades made with trial funds or additional funds |
| userLevel | int64 | Customer level |
| commissionRatio | int64 | Commission percentage, unit: % |
| currentBenefit | int64 | Current welfare method: 0 - No welfare, 1 - Fee cashback, 2 - Perpetual fee discount |
| benefitRatio | int64 | Transaction fee reduction percentage, unit: % |
| benefitExpiration | long | Welfare expiration timestamp, unit: milliseconds |

**Request Example**

```json
{
  "uid": "1645382"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "SUCCESS",
  "timestamp": 1689579799063,
  "data": {
    "uid": 2489544,
    "existInviter": "true",
    "inviteResult": true,
    "registerDateTime": 1656208955000,
    "directInvitation": false,
    "superiorsUid": 2293934,
    "deposit": true,
    "kycResult": "false",
    "trade": true,
    "userLevel": 2,
    "commissionRatio": 20,
    "currentBenefit": 0,
    "benefitRatio": 0,
    "benefitExpiration": 0
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/agent/v1/account/inviteRelationCheck'
    method = "GET"
    paramsMap = {
    "uid": "1645382"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query the deposit details of invited users

**GET** `/openApi/agent/v1/account/inviteRelationCheck`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| uid | long | Yes | Inviting user UID, must be the parent user UID |
| bizType | int64 | Yes | 1:Deposit |
| startTime | int64 | Yes | Start timestamp (days), only supports querying the last 90 days of data. |
| endTime | int64 | Yes | End timestamp (days). Only the last 90 days of data can be queried. |
| pageIndex | int64 | Yes | Page number for pagination, must be greater than 0 |
| pageSize | int64 | Yes | The number of pages must be greater than 0 and the maximum value is 100 |
| recvWindow | int64 | No | Request valid time window value, unit: milliseconds. If not filled, the default is 5 seconds |
| timestamp | int64 | Yes | request timestamp, unit: millisecond |

**Response Body**

| filed | data type | description |
|---|---|---|
| uid | long | Invited User UID |
| inviteResult | boolean | true: invitation relationship,false: non-invitation relationship |
| directInvitation | boolean | true: Direct invitation, false: Indirect invitation |
| bizType | int64 | 1:Deposi |
| bizTime | long | event time |
| assetType | int64 | Operation type breakdown |
| assetTypeName | string | Operation type subdivision name |
| currencyName | string | Currency |
| currencyAmountVolume | string | amount |

**Request Example**

```json
{
  "uid": "1645382",
  "startTime": "1699183026000",
  "endTime": "1699269426000",
  "bizType": "1",
  "recWindow": "6000"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "SUCCESS",
  "timestamp": 1689579799063,
  "data": {
    "list": [
      {
        "uid": 2489544,
        "inviteResult": true,
        "directInvitation": true,
        "bizType": 1,
        "bizTime": 1673674073000,
        "assetType": 30,
        "assetTypeName": "Deposit",
        "currencyName": "USDT",
        "currencyAmountVolume": "1000"
      }
    ],
    "total": 1
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/agent/v1/account/inviteRelationCheck'
    method = "GET"
    paramsMap = {
    "uid": "1645382",
    "startTime": "1699183026000",
    "endTime": "1699269426000",
    "bizType": "1",
    "recWindow": "6000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query API transaction commission （non-invitation relationship）

**GET** `/openApi/agent/v1/reward/third/commissionDataList`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| uid | long | No | UID of the trading user (non-invitation relationship user) |
| commissionBizType | int64 | Yes | 81: perpetual contract trading API commission 82: spot trading API commission |
| startTime | date | Yes | Start timestamp (days), Only supports querying data after December 1, 2023. |
| endTime | date | Yes | End timestamp (days). Only supports querying data after December 1, 2023. |
| pageIndex | int64 | Yes | Page number for pagination, must be greater than 0 |
| pageSize | int64 | Yes | The number of pages must be greater than 0 and the maximum value is 100 |
| recvWindow | int64 | No | Request valid time window value, unit: milliseconds. If not filled, the default is 5 seconds |
| timestamp | int64 | Yes | request timestamp, unit: millisecond |

**Response Body**

| filed | data type | description |
|---|---|---|
| uid | long | UID of the trading user (non-invitation relationship user) |
| commissionTime | long | Commission timestamp, date |
| tradeVolume | string | API order amount is discounted in USDT |
| commissionVolume | string | ebate commission amount in USDT |
| commissionBizType | int64 | 81: perpetual contract trading API commission 82: spot trading API commission |

**Request Example**

```json
{
  "uid": "1645382",
  "startTime": "1699183026000",
  "endTime": "1699269426000",
  "commissionBizType": "81",
  "recWindow": "6000"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "SUCCESS",
  "timestamp": 1689579799063,
  "data": {
    "list": [
      {
        "uid": 25053735,
        "commissionTime": 1700759104737,
        "tradeVolume": "10.234",
        "commissionVolume": "0.02663866",
        "commissionBizType": 81
      }
    ],
    "total": 3
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/agent/v1/reward/third/commissionDataList'
    method = "GET"
    paramsMap = {
    "uid": "1645382",
    "startTime": "1699183026000",
    "endTime": "1699269426000",
    "commissionBizType": "81",
    "recWindow": "6000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query partner information

**GET** `/openApi/agent/v1/asset/partnerData`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| uid | long | No | Partner UID |
| startTime | int64 | No | Start time, unit: day, only supports querying the latest 3 months. |
| endTime | int64 | No | End time, unit: day, only supports querying the latest 3 months. |
| pageIndex | int64 | No | 如果未填寫，預設值為1 |
| pageSize | int64 | No | the maximum value is 200 |
| recvWindow | int64 | No | Request valid time window value, unit: milliseconds. If not filled, the default is 5 seconds |
| timestamp | int64 | Yes | request timestamp, unit: millisecond |

**Response Body**

| filed | data type | description |
|---|---|---|
| uid | long | Partner UID |
| email | STRING | Partner mailbox, encrypted status |
| Phone | STRING | Partner's mobile phone number,Partner's mobile phone number, encrypted |
| referralType | int64 | Invitation type: 1: direct invitation, 2: indirect invitation |
| remarks | STRING | Remarks |
| referrerUid | long | Superior Uid |
| language | STRING | language |
| newReferees | STRING | The number of new invitees during the query period |
| firstTrade | STRING | Number of people who made their first transaction during the query period |
| branchDeposits | STRING | The amount of channel recharge during the query period |
| branchTrading | STRING | Number of channel transactions during query time |
| branchTradingVol | STRING | The transaction amount of the channel during the query period |
| level | STRING | level |
| commissionRatio | STRING | Rebate ratio |

**Request Example**

```json
{
  "startTime": "1699183026000",
  "endTime": "1699269426000",
  "pageIndex": "1",
  "pageSize": "100",
  "recWindow": "6000"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1718441614690,
  "data": {
    "list": [
      {
        "uid": 25414560,
        "email": "jo***@gmail.com",
        "phone": "*******7294",
        "referralType": 1,
        "remarks": "123",
        "referrerUid": 24186664,
        "language": "en",
        "newReferees": 0,
        "firstTrade": 0,
        "branchDeposits": "24534.446799999998",
        "branchTrading": 4,
        "branchTradingVol": "98434310.99579316",
        "level": 0,
        "commissionRatio": 0.04
      }
    ],
    "total": 1
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/agent/v1/asset/partnerData'
    method = "GET"
    paramsMap = {
    "startTime": "1699183026000",
    "endTime": "1699269426000",
    "pageIndex": "1",
    "pageSize": "100",
    "recWindow": "6000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Invitation code data

**GET** `/openApi/agent/v1/commissionDataList/referralCode`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| referralCode | string | No | Invitation code; if left blank, query all. |
| directInvitation | string | Yes | Invitation relationship, true: direct invitation, false: indirect invitation |
| startTime | Long | No | Start time only supports querying data for the most recent year. If neither startTime nor endTime is filled in, the default is to return data for the most recent 7 days. The maximum query time window is 92 days |
| endTime | Long | No | End time only supports querying data for the most recent year. If neither startTime nor endTime is filled in, the default is to return data for the most recent 7 days. The maximum query time window is 92 days |
| pageIndex | int64 | No | Number of pages, default is 1 if not specified |
| pageSize | int64 | No | Number of pages per page, default is 100 if not specified, maximum is 200 |
| recvWindow | int64 | No | Request valid time window value, unit: milliseconds |
| timestamp | int64 | Yes | Timestamp of the request, in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| referralCode | string | Invitation code |
| commissionRatio | STRING | Commission percentage, unit: % |
| friendEarn | STRING | Friend cashback ratio, unit: % |
| swapFeeDiscount | STRING | Futures fee discount ratio, unit: % |
| referralNum | STRING | Number of invitees |
| deposited | STRING | Number of users who have deposited |
| traded | STRING | Number of users who have traded |
| tradingVolume | STRING | Transaction amount |
| fee | STRING | Fee |
| offsetTradingFees | STRING | Fee deduction |
| payableTradingFees | STRING | Actual transaction fee paid |
| commission | STRING | Your commission |

**Request Example**

```json
{
  "referralCode": "LYA2025",
  "directInvitation": "true",
  "startTime": "1699183026000",
  "endTime": "1699269426000",
  "pageIndex": "1",
  "pageSize": "100",
  "recWindow": "6000"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1718441614690,
  "data": {
    "list": [
      {
        "referralCode": "LYA2025",
        "commissionRatio": "50",
        "friendEarn": "45",
        "swapFeeDiscount": "30",
        "referralNum": "8",
        "deposited": "3",
        "traded": "6",
        "tradingVolume": "24534.446799999998",
        "fee": "120.492",
        "offsetTradingFees": "120.492",
        "payableTradingFees": "120.492",
        "commission": "10.040000"
      }
    ]
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/agent/v1/commissionDataList/referralCode'
    method = "GET"
    paramsMap = {
    "referralCode": "LYA2025",
    "directInvitation": "true",
    "startTime": "1699183026000",
    "endTime": "1699269426000",
    "pageIndex": "1",
    "pageSize": "100",
    "recWindow": "6000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Superior verification

**GET** `/openApi/agent/v1/account/superiorCheck`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| uid | long | Yes | The account uid of the superior |

**Response Body**

| filed | data type | description |
|---|---|---|
| inviteResult | boolean | true: invitation relationship,false: non-invitation relationship |
| directInvitation | boolean | true: Direct invitation, false: Indirect invitation |

**Request Example**

```json
{
  "uid": "1645382"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "SUCCESS",
  "timestamp": 1689579799063,
  "data": {
    "inviteResult": true,
    "directInvitation": false
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/agent/v1/account/superiorCheck'
    method = "GET"
    paramsMap = {
    "uid": "1645382"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

### Copy Trade

#### USDT-M Perpetual Contracts

#### Trader’s current order

**GET** `/openApi/copyTrading/v1/swap/trace/currentTrack`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | Yes | Trading pair, e.g. BTC-USDT, please use uppercase letters. |
| offset | int64 | No | Offset, default is 0. |
| limit | int64 | No | Number of records to query, default is 20, maximum is 50. |
| timestamp | int64 | No | Request timestamp, in milliseconds. |
| recvWindow | int64 | Yes | Request valid time window, in milliseconds. Default is 5 seconds if not provided. |

**Response Body**

| filed | data type | description |
|---|---|---|
| orderId | int64 | Perpetual business order number |
| positionId | int64 | With order number |
| symbol | string | symbol |
| marginType | string | Margin mode, isolated position: ISOLATED, cross position: CROSSED |
| positionSide | string | Position side |
| openLeverage | string | open leverage |
| openAvgPrice | string | average opening price |
| markPrice | string | mark price |
| openTime | int64 | Opening time |
| volume | string | Position quantity |
| margain | string | Margin amount |
| unrealizedProfit | string | unrealized profit or loss |
| profitRatio | string | profit, in% |
| stopProfitPrice | string | Take profit price, empty if not set |
| stopLossPrice | string | Stop loss price, empty if not set |

**Request Example**

```json
{
  "recvWindow": "0",
  "symbol": "BTC-USDT"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1702731524284,
  "data": {
    "result": [
      {
        "orderId": 1735671429301234700,
        "positionId": 1253243912971234600,
        "volume": "0.0041",
        "openAvgPrice": "42113.4000000000000",
        "unrealizedProfit": "+1.2169",
        "openTime": 1702651291745,
        "stopLossPrice": "",
        "symbol": "BTC-USDT",
        "profitRatio": "+0.70%",
        "openLeverage": "20",
        "marginType": "CROSSED",
        "margain": "8.633247",
        "positionSide": "Long",
        "stopProfitPrice": "",
        "markPrice": "42410.22424947234685532749"
      },
      {
        "orderId": 1735671429301234700,
        "positionId": 1253243912971234600,
        "volume": "0.0041",
        "openAvgPrice": "42113.4000000000000",
        "unrealizedProfit": "+1.2169",
        "openTime": 1702651291398,
        "stopLossPrice": "",
        "symbol": "BTC-USDT",
        "profitRatio": "+0.70%",
        "openLeverage": "20",
        "marginType": "CROSSED",
        "margain": "8.633247",
        "positionSide": "Long",
        "stopProfitPrice": "",
        "markPrice": "42410.22424947234685532749"
      },
      {
        "orderId": 1735671429301234700,
        "positionId": 1253243912971234600,
        "volume": "0.0014",
        "openAvgPrice": "42108.2000000000000",
        "unrealizedProfit": "+0.4228",
        "openTime": 1702651291040,
        "stopLossPrice": "",
        "symbol": "BTC-USDT",
        "profitRatio": "+0.71%",
        "openLeverage": "20",
        "marginType": "CROSSED",
        "margain": "2.947574",
        "positionSide": "Long",
        "stopProfitPrice": "",
        "markPrice": "42410.22424947234685532749"
      },
      {
        "orderId": 1735671429301234700,
        "positionId": 1253243912971234600,
        "volume": "0.0014",
        "openAvgPrice": "42107.7000000000000",
        "unrealizedProfit": "+0.4235",
        "openTime": 1702651290638,
        "stopLossPrice": "",
        "symbol": "BTC-USDT",
        "profitRatio": "+0.71%",
        "openLeverage": "20",
        "marginType": "CROSSED",
        "margain": "2.947539",
        "positionSide": "Long",
        "stopProfitPrice": "",
        "markPrice": "42410.22424947234685532749"
      }
    ],
    "searchResult": true,
    "total": 4
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/copyTrading/v1/swap/trace/currentTrack'
    method = "GET"
    paramsMap = {
    "recvWindow": "0",
    "symbol": "BTC-USDT"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Traders close positions according to the order number

**POST** `/openApi/copyTrading/v1/swap/trace/closeTrackOrder`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| positionId | int64 | Yes | Order number with order |
| timestamp | int64 | No | Request timestamp in milliseconds |
| recvWindow | int64 | Yes | Request valid time empty window value, unit: milliseconds, default to 5 seconds if left blank |

**Response Body**

| filed | data type | description |
|---|---|---|
| positionId | int64 | Order number with order |

**Request Example**

```json
{
  "positionId": "1252864099381234567",
  "recvWindow": "5000"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1702575099575,
  "data": {
    "positionId": 1252864099381234700
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/copyTrading/v1/swap/trace/closeTrackOrder'
    method = "POST"
    paramsMap = {
    "positionId": "1252864099381234567",
    "recvWindow": "5000"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Traders set take profit and stop loss based on order numbers

**POST** `/openApi/copyTrading/v1/swap/trace/setTPSL`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| positionId | int64 | Yes | Order number with order |
| takeProfitMarkPrice | float64 | Yes | Set the price of the stop profit and stop loss mark, and the price of the stop profit and stop loss mark must be one of two options |
| stopLossMarkPrice | float64 | Yes | Set a stop loss marker price, and the stop loss marker price must be either |
| timestamp | int64 | No | Request timestamp in milliseconds |
| recvWindow | int64 | Yes | Request valid time empty window value, unit: milliseconds, default to 5 seconds if left blank |

**Response Body**

| filed | data type | description |
|---|---|---|
| positionId | int64 | Order number with order |
| takeProfitMarkPrice | float64 | Set the price of the stop profit and stop loss mark, and the price of the stop profit and stop loss mark must be one of two options |
| stopLossMarkPrice | float64 | Set a stop loss marker price, and the stop loss marker price must be either |

**Request Example**

```json
{
  "positionId": "1253517936071234567",
  "recvWindow": "0",
  "stopLossMarkPrice": "105.38"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1702731523011,
  "data": {
    "positionId": 1253517936071234600,
    "stopLossMarkPrice": 105.38
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/copyTrading/v1/swap/trace/setTPSL'
    method = "POST"
    paramsMap = {
    "positionId": "1253517936071234567",
    "recvWindow": "0",
    "stopLossMarkPrice": "105.38"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Personal Trading Overview

**GET** `/openApi/copyTrading/v1/PFutures/traderDetail`

- **Rate Limit**: UID Rate Limit 10s/s / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| daySize | int64 | No | Profit rate over the last N days, N must be 7, 30, 90, or 180 |

**Response Body**

| filed | data type | description |
|---|---|---|
| contractType | string | Contract type, SFUTURES: Standard Contract, PFUTURES: USD-Margined Contract |
| traderId | string | Trader ID |
| status | string | true: can follow, false: cannot follow |
| accountLevel | string | Account copy trading level (Bronze, Silver, Gold, Diamond) |
| ratio | decimal | Profit rate over the last N days, in % |
| accountAssets | string | Account assets converted to USDT, with up to 15 minutes delay |
| copierProfit | string | Copy trading profit |
| copiersNum | int64 | Number of followers |
| riskLevel | int64 | Risk level (1-9), higher number means higher risk |
| winRatio | decimal | Winning rate |
| tradeNum | int64 | Total number of trades |
| winNum | int64 | Number of winning trades |
| loseNum | int64 | Number of losing trades |
| averageProfit | string | Average profit |
| averageLosses | string | Average loss |
| PnlRatio | string | Profit and loss ratio |
| averageTime | decimal | Average holding time, in hours |
| marginMedian | decimal | Median margin |
| leverageMedian | int64 | Median leverage |
| tradeFrequency | decimal | Weekly trade frequency |
| tradeDays | int64 | Number of trading days |
| lastTrade | long | Timestamp of the last trade |

**Request Example**

```json
{
  "daySize": 7
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "success",
  "timestamp": 1711619555065,
  "data": {
    "contractType": "PFUTURES",
    "traderId": "123456",
    "status": "true",
    "accountLevel": "Gold",
    "ratio": "5.32",
    "accountAssets": "10000.25",
    "copierProfit": "125.67",
    "copiersNum": 154,
    "riskLevel": 3,
    "winRatio": "68.2",
    "tradeNum": 325,
    "winNum": 221,
    "loseNum": 104,
    "averageProfit": "75.25",
    "averageLosses": "45.12",
    "PnlRatio": "1.67",
    "averageTime": 3.8,
    "marginMedian": 250,
    "leverageMedian": 10,
    "tradeFrequency": 4.2,
    "tradeDays": 85,
    "lastTrade": 1711619555065
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/copyTrading/v1/PFutures/traderDetail'
    method = "GET"
    paramsMap = {
    "daySize": 7
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Profit Overview

**GET** `/openApi/copyTrading/v1/PFutures/profitHistorySummarys`

- **Rate Limit**: UID Rate Limit 10s/s / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| filed | data type | description |  |

**Request Example**

```json
{}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "success",
  "timestamp": 1711619555065,
  "data": {
    "contractType": "PFUTURES",
    "earn": "158.32",
    "settled": "10253.55",
    "profitRatio": "12.5"
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/copyTrading/v1/PFutures/profitHistorySummarys'
    method = "GET"
    paramsMap = {}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Profit Details

**GET** `/openApi/copyTrading/v1/PFutures/profitDetail`

- **Rate Limit**: UID Rate Limit 10s/s / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| startTime | int64 | No | Start timestamp for profit distribution, in milliseconds. Queries profits within the time range. |
| endTime | int64 | No | End timestamp for profit distribution, in milliseconds. Queries profits within the time range. |
| pageIndex | int64 | Yes | Page number, must be greater than 0 |
| pageSize | int64 | Yes | Number of items per page, must be greater than 0, maximum 100 |

**Response Body**

| filed | data type | description |
|---|---|---|
| contractType | string | Contract type, SFUTURES: Standard Contract, PFUTURES: USD-Margined Contract |
| commissionTime | long | Profit distribution timestamp, in seconds |
| CopiersUid | string | Follower UID |
| profitShare | string | Profit share amount (USDT) |

**Request Example**

```json
{
  "startTime": 1711000000000,
  "endTime": 1711619555000,
  "pageIndex": 1,
  "pageSize": 20
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "success",
  "timestamp": 1711619555065,
  "data": [
    {
      "contractType": "PFUTURES",
      "commissionTime": 1711600000,
      "CopiersUid": "987654321",
      "profitShare": "12.35"
    },
    {
      "contractType": "PFUTURES",
      "commissionTime": 1711500000,
      "CopiersUid": "123456789",
      "profitShare": "8.77"
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/copyTrading/v1/PFutures/profitDetail'
    method = "GET"
    paramsMap = {
    "startTime": 1711000000000,
    "endTime": 1711619555000,
    "pageIndex": 1,
    "pageSize": 20
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Set Commission Rate

**POST** `/openApi/copyTrading/v1/PFutures/setCommission`

- **Rate Limit**: UID Rate Limit 10s/s / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| newCommission | string | Yes | The commission rate to set, must be greater than 10% and less than the current level. Silver level: 16%, Gold level: 20%, Diamond level: 32% |

**Response Body**

| filed | data type | description |
|---|---|---|
| newCommission | string | The newly set commission rate |

**Request Example**

```json
{
  "newCommission": "16%"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "success",
  "timestamp": 1711619555065,
  "data": {
    "newCommission": "16%"
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/copyTrading/v1/PFutures/setCommission'
    method = "POST"
    paramsMap = {
    "newCommission": "16%"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Trader Gets Copy Trading Pairs

**GET** `/openApi/copyTrading/v1/PFutures/tradingPairs`

- **Rate Limit**: UID Rate Limit 10s/s / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| contractType | string | Yes | Contract type, SFUTURES: Standard contract, PFUTURES: USDT-margined contract |

**Response Body**

| filed | data type | description |
|---|---|---|
| contractType | string | Contract type, SFUTURES: Standard contract, PFUTURES: USDT-margined contract |
| symbol | string | Trading pair |
| openTrader | string | Whether copy trading is enabled, yes: enabled, no: disabled |
| minOpenCount | string | Minimum number of orders a trader can open |
| maxLeverage | string | Maximum leverage a trader can use for opening orders |
| stopSurplusRatio | string | Take-profit ratio setting |
| stopLossRatio | string | Stop-loss ratio setting |

**Request Example**

```json
{
  "contractType": "PFUTURES"
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "success",
  "timestamp": 1711619555065,
  "data": [
    {
      "contractType": "PFUTURES",
      "symbol": "BTCUSDT",
      "openTrader": "yes",
      "minOpenCount": "1",
      "maxLeverage": "125",
      "stopSurplusRatio": "50",
      "stopLossRatio": "30"
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/copyTrading/v1/PFutures/tradingPairs'
    method = "GET"
    paramsMap = {
    "contractType": "PFUTURES"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Spot Trading

#### Trader sells spot assets based on buy order number

**POST** `/openApi/copyTrading/v1/spot/trader/sellOrder`

- **Rate Limit**: UID Rate Limit 10/second / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| orderId | int64 | Yes | Trader's spot buy order number |

**Response Body**

| filed | data type | description |
|---|---|---|
| orderNo | int64 | Transaction order number |
| price | float64 | Price passed by the user |
| dealPrice | float64 | Average transaction price |
| coinName | string | Name of the trading coin, such as BTC |
| status | int8 | Order status 5 Not triggered 10 Processing 11 In commission 20 Cancelling 30 Success 31 Cancelled 40 Failed |

**Request Example**

```json
{
  "orderId": "1253517936071234567"
}
```

**Response Example**

```json
{
  "code": 0,
  "timestamp": 1711619555065,
  "data": {
    "orderNo": 1773285851363541000,
    "coinName": "BTC",
    "valuationCoinName": "USDT",
    "side": 2,
    "price": "70850",
    "dealPrice": "70612.7438655",
    "delegatePrice": "70613.45",
    "status": 30
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/copyTrading/v1/spot/trader/sellOrder'
    method = "POST"
    paramsMap = {
    "orderId": "1253517936071234567"
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Personal Trading Overview

**GET** `/openApi/copyTrading/v1/PFutures/traderDetail`

- **Rate Limit**: UID Rate Limit 10s/s / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| daySize | int64 | No | Profit rate over the last N days, N must be 7, 30, 90, or 180 |

**Response Body**

| filed | data type | description |
|---|---|---|
| contractType | string | Contract type, SFUTURES: Standard Contract, PFUTURES: USD-Margined Contract |
| traderId | string | Trader ID |
| status | string | true: can follow, false: cannot follow |
| accountLevel | string | Account copy trading level (Bronze, Silver, Gold, Diamond) |
| ratio | decimal | Profit rate over the last N days, in % |
| accountAssets | string | Account assets converted to USDT, with up to 15 minutes delay |
| copierProfit | string | Copy trading profit |
| copiersNum | int64 | Number of followers |
| riskLevel | int64 | Risk level (1-9), higher number means higher risk |
| winRatio | decimal | Winning rate |
| tradeNum | int64 | Total number of trades |
| winNum | int64 | Number of winning trades |
| loseNum | int64 | Number of losing trades |
| averageProfit | string | Average profit |
| averageLosses | string | Average loss |
| PnlRatio | string | Profit and loss ratio |
| averageTime | decimal | Average holding time, in hours |
| marginMedian | decimal | Median margin |
| leverageMedian | int64 | Median leverage |
| tradeFrequency | decimal | Weekly trade frequency |
| tradeDays | int64 | Number of trading days |
| lastTrade | long | Timestamp of the last trade |

**Request Example**

```json
{
  "daySize": 7
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "success",
  "timestamp": 1711619555065,
  "data": {
    "contractType": "PFUTURES",
    "traderId": "123456",
    "status": "true",
    "accountLevel": "Gold",
    "ratio": "5.32",
    "accountAssets": "10000.25",
    "copierProfit": "125.67",
    "copiersNum": 154,
    "riskLevel": 3,
    "winRatio": "68.2",
    "tradeNum": 325,
    "winNum": 221,
    "loseNum": 104,
    "averageProfit": "75.25",
    "averageLosses": "45.12",
    "PnlRatio": "1.67",
    "averageTime": 3.8,
    "marginMedian": 250,
    "leverageMedian": 10,
    "tradeFrequency": 4.2,
    "tradeDays": 85,
    "lastTrade": 1711619555065
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/copyTrading/v1/PFutures/traderDetail'
    method = "GET"
    paramsMap = {
    "daySize": 7
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Profit Summary

**GET** `/openApi/copyTrading/v1/spot/profitHistorySummarys`

- **Rate Limit**: UID Rate Limit 10s/s / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| filed | data type | description |  |

**Request Example**

```json
{}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "success",
  "timestamp": 1711619555065,
  "data": {
    "earn": "100.0",
    "settled": "500.0",
    "profitRatio": 0.2
  }
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/copyTrading/v1/spot/profitHistorySummarys'
    method = "GET"
    paramsMap = {}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Profit Details

**GET** `/openApi/copyTrading/v1/PFutures/profitDetail`

- **Rate Limit**: UID Rate Limit 10s/s / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| startTime | int64 | No | Start timestamp for profit distribution, in milliseconds. Queries profits within the time range. |
| endTime | int64 | No | End timestamp for profit distribution, in milliseconds. Queries profits within the time range. |
| pageIndex | int64 | Yes | Page number, must be greater than 0 |
| pageSize | int64 | Yes | Number of items per page, must be greater than 0, maximum 100 |

**Response Body**

| filed | data type | description |
|---|---|---|
| contractType | string | Contract type, SFUTURES: Standard Contract, PFUTURES: USD-Margined Contract |
| commissionTime | long | Profit distribution timestamp, in seconds |
| CopiersUid | string | Follower UID |
| profitShare | string | Profit share amount (USDT) |

**Request Example**

```json
{
  "startTime": 1711000000000,
  "endTime": 1711619555000,
  "pageIndex": 1,
  "pageSize": 20
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "success",
  "timestamp": 1711619555065,
  "data": [
    {
      "contractType": "PFUTURES",
      "commissionTime": 1711600000,
      "CopiersUid": "987654321",
      "profitShare": "12.35"
    },
    {
      "contractType": "PFUTURES",
      "commissionTime": 1711500000,
      "CopiersUid": "123456789",
      "profitShare": "8.77"
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/copyTrading/v1/PFutures/profitDetail'
    method = "GET"
    paramsMap = {
    "startTime": 1711000000000,
    "endTime": 1711619555000,
    "pageIndex": 1,
    "pageSize": 20
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### Query Historical Orders

**GET** `/openApi/copyTrading/v1/spot/historyOrder`

- **Rate Limit**: UID Rate Limit 10s/s / UID

**Hosts**

| PROD | HOST |
|---|---|
| PROD | https://open-api.bingx.com |
| VST | https://open-api-vst.bingx.com |

**Request Parameters**

| REQUEST PARAMETER | data type | required | description |
|---|---|---|---|
| symbol | string | No | Trading pair |
| startTime | int64 | No | Start timestamp in milliseconds, query orders within the time range |
| endTime | int64 | No | End timestamp in milliseconds, query orders within the time range |
| pageIndex | int64 | Yes | Page index, must be greater than 0 |
| pageSize | int64 | Yes | Number of items per page, must be greater than 0, maximum 100 |
| recvWindow | long | No | Request valid window in milliseconds |

**Response Body**

| filed | data type | description |
|---|---|---|
| openOrderId | string | Buy order ID |
| closeOrderId | string | Sell order ID |
| symbol | string | Trading pair |
| quantity | string | Quantity |
| Amount | string | Amount |
| profit | string | Realized profit/loss |
| openPrice | string | Average buy price |
| closeTime | long | Sell time |
| closePrice | string | Average sell price |

**Request Example**

```json
{
  "pageIndex": 1,
  "pageSize": 50
}
```

**Response Example**

```json
{
  "code": 0,
  "msg": "success",
  "timestamp": 1711619555065,
  "data": [
    {
      "openOrderId": "123456",
      "closeOrderId": "123457",
      "symbol": "BTCUSDT",
      "quantity": "0.5",
      "Amount": "35000",
      "profit": "500",
      "openPrice": "70000",
      "closeTime": 1711619555065,
      "closePrice": "71000"
    }
  ]
}
```

**Python Demo**

```python
import time
import requests
import hmac
import urllib.parse
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = ""
SECRETKEY = ""

def demo():
    payload = {}
    path = '/openApi/copyTrading/v1/spot/historyOrder'
    method = "GET"
    paramsMap = {
    "pageIndex": 1,
    "pageSize": 50
}
    paramsStr, urlParamsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, urlParamsStr, payload)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def send_request(method, path, paramsStr, urlParamsStr, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlParamsStr, get_sign(SECRETKEY, paramsStr))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsList = []
    urlParamsList = []
    for x in sortedKeys:
        value = paramsMap[x]
        paramsList.append("%s=%s" % (x, value))
    timestamp = str(int(time.time() * 1000))
    paramsStr = "&".join(paramsList)
    if paramsStr != "": 
        paramsStr = paramsStr + "&timestamp=" + timestamp
    else:
        paramsStr = "timestamp=" + timestamp
    contains = '[' in paramsStr or '{' in paramsStr
    for x in sortedKeys:
        value = paramsMap[x]
        if contains:
            encodedValue = urllib.parse.quote(str(value), safe='')
            urlParamsList.append("%s=%s" % (x, encodedValue))
        else:
            urlParamsList.append("%s=%s" % (x, value))
    urlParamsStr = "&".join(urlParamsList)
    if urlParamsStr != "": 
        urlParamsStr = urlParamsStr + "&timestamp=" + timestamp
    else:
        urlParamsStr = "timestamp=" + timestamp
    return paramsStr, urlParamsStr


if __name__ == '__main__':
    print("demo:", demo())
```

---

#### CHANGE LOGS

---
