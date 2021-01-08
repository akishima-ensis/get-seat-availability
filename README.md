# get-seat-availability

![deploy](https://github.com/akishima-ensis/get-seat-availability/workflows/deploy/badge.svg)

## About
アキシマエンシス（昭島市教育福祉総合センター）の学習室における空席状況を取得するためのスクリプトです。

取得したデータは以下のリポジトリで使用されています。

・学習室の空席状況をリアルタイムで取得できるLINE Bot（[seat-availability-check-linebot](https://github.com/akishima-ensis/seat-availability-check-linebot)）

・学習室の1日分の空席状況を可視化したWebサイト（[seat-availability-checker](https://github.com/akishima-ensis/seat-availability-checker)）

## How it works

[昭島市民図書館](https://webreserv.library.akishima.tokyo.jp/webReserv/AreaInfo/Login)に対してリクエストを送り、取得したHTMLから各学習室の空席状況を抽出しCloudFirestoreに保存するというスクリプトです。このスクリプトはCloudFunctionsにデプロイされており、CloudSchedulerを用いて開館時間（10:00〜20:00）に１分間隔で実行されます。

![](https://user-images.githubusercontent.com/34241526/102766664-d965ab00-43c1-11eb-8bb3-23f6223c6806.png)

[diagrams.net](https://app.diagrams.net/)
