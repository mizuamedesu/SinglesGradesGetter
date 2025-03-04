## セットアップ
```
docker compose up --build
```
## WebUI

http://localhost:8080/

## APIエンドポイント

```
curl -X POST http://localhost:8080/grades -H "Content-Type: application/json" -d "{\"twins_user\": \"your_username\", \"twins_pass\": \"your_password\"}"
```

## 何ができるのか？

全ての成績をjson形式で吐け出せます。

```
  {
    "No.": "14",
    "年度": "2024",
    "学期": "秋学期",
    "科目区分": "専門科目",
    "科目番号": "GB27001",
    "科目名": "ソフトウェアサイエンス特別講義A",
    "主担当教員": "伊藤 誠",
    "単位数": "1.0",
    "春学期": "-",
    "秋学期": "-",
    "評点": "",
    "総合": "B"
  }
```

## 注意

実在する組織、団体、ウェブサイト等とは一切関係ありません。実行によって生じた一切の責任を負いません。