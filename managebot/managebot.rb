
require 'net/http'
require 'uri'
require 'json'
require 'discordrb'

TOKEN = ENV['TOKEN']
CHANNEL_ID = ENV['CHANNEL_ID'].to_i
PASSWORD=ENV['NETTOOL_PASSWORD']

bot = Discordrb::Bot.new(token: TOKEN, intents: [:server_messages, :direct_messages])

bot.message(content: "!overwrite", in: CHANNEL_ID) do |event|
  file = event.message.attachments[0]
  if file.nil?
    event.respond "ファイルが添付されていません。"
    return
  end
  tmpname = Time.now.strftime('%Y-%m-%d_%H-%M-%S')
  event.respond <<~EOS
    以下のファイルでセーブデータを上書きし、ゲームを再起動します。
    name: #{file.filename}
    size: #{file.size}
    url: #{file.url}
  EOS
  puts `mkdir -p tmp`
  # ブラウザからのリクエストを模倣する
  CURL = <<~EOS
    curl -o tmp/#{tmpname}.sve '#{file.url}' \
    -H 'accept: image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8' \
    -H 'accept-language: ja,en-US;q=0.9,en;q=0.8' \
    -H 'dnt: 1' \
    -H 'if-modified-since: Fri, 21 Feb 2025 06:15:40 GMT' \
    -H 'if-none-match: "751e6f857b21182ccc7c97ecc6b9e7e0"' \
    -H 'priority: i' \
    -H 'sec-ch-ua: "Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"' \
    -H 'sec-ch-ua-mobile: ?0' \
    -H 'sec-ch-ua-platform: "Linux"' \
    -H 'sec-fetch-dest: image' \
    -H 'sec-fetch-mode: no-cors' \
    -H 'sec-fetch-site: same-origin' \
    -H 'user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
  EOS
  puts `#{CURL}`
  puts `mv ../simutrans/server13353-network.sve ../simutrans/save/overwrite-#{tmpname}-origin.sve`
  puts `cp tmp/#{tmpname}.sve ../simutrans/server13353-network.sve`
  puts `cp tmp/#{tmpname}.sve ../simutrans/save/overwrite-#{tmpname}-new.sve`
  puts `docker restart nanasaba1st-simutrans-server-1`
  event.respond "セーブデータを上書きしました。"
end

bot.message(content: "!restart", in: CHANNEL_ID) do |event|
  # ここで自動セーブを入れる
  puts `../nettool -s simutrans-server -p #{PASSWORD} force-sync`
  event.respond "自動セーブを実行中です。しばらくお待ちください。"
  sleep 1
  puts `../nettool -s simutrans-server -p #{PASSWORD} clients`
  puts `docker restart nanasaba1st-simutrans-server-1`
  event.respond "再起動しました。"
end

bot.message(start_with: "!chat") do |event|
  uri = URI('http://llm:8000/chat')
  headers = { 'Content-Type' => 'application/json' }
  data = {
    input: event.message.content.gsub(/^!chat /, ''),
  }

  text = "読み込み中..."
  messages = nil

  progress = event.respond "読み込み中です。しばらくお待ち下さい。"

  Thread.new do
    start = Time.now
    while messages.nil? && Time.now - start < 100
      sleep 3
      text += "." if text[-1] == "."
      progress.edit(text)
    end
    sleep 5
    progress.delete
  end

  Net::HTTP.start(uri.host, uri.port) do |http|
    request = Net::HTTP::Post.new(uri, headers)
    request.body = data.to_json

    http.request(request) do |response|
      response.read_body do |chunk|
        chunk.each_line do |line|
          puts line.strip unless line.strip.empty?
          STDOUT.flush

          begin
            data = JSON.parse(line)
          rescue JSON::ParserError => e
            puts "JSON parse error: #{e.message}"
            next
          end
          if data['type'] == 'start'
            text += "読み込み終了..."
          elsif data['type'] == 'chunk'
            text += data['content'].gsub(/\s+/, ' ')
          elsif data['type'] == 'tool_start'
            text += data['name'] + "を実行中..."
          elsif data['type'] == 'tool_end'
            text += data['name'] + "を実行完了..."
          elsif data['type'] == 'end'
            text += "終了"
          elsif data['type'] == 'result'
            messages = data['messages']
          end
        end
      end
    end
  end

  # ログ出力
  messages.each do |message|
    if message['type'] == 'human'
      puts "human: #{message['content']}"
    elsif message['type'] == 'ai'
      puts "ai: #{message['content']}"
    elsif message['type'] == 'tool_call'
      puts "tool_call:"
      puts "  name: #{message['name']}"
      puts "  args: #{message['args']}"
    elsif message['type'] == 'tool'
      puts "tool: #{message['content']}"
    end
  end
  STDOUT.flush

  begin
    # <result>...</result>の間にあるJSONをパースする
    body = messages.last['content'].match(/<result>(.*?)<\/result>/m)
    if body.nil? || body[1].nil?
      response = JSON.parse(messages.last['content']) # <result>タグがないので、とりあえずそのままパース
    else
      response = JSON.parse(body[1]) # <result>タグの中身をパース
    end
  rescue JSON::ParserError => e
    puts "JSON parse error: #{e.message}"
    event.respond messages.last['content'] # パースできなかった場合はそのまま表示する
    next
  end
  images = response['images']
  image_files = images.flat_map do |id|
    begin
      [File.open("/data/#{id}.png", 'r')]
    rescue Errno::ENOENT
      puts "File not found: /data/#{id}.png"
      []
    end
  end
  if response['message'].chomp.empty?
    final_response = "処理が完了しました。"
  else
    final_response = response['message']
  end
  # なぜかfalseとnilを指定しないとInvalid Form Bodyエラーになる
  event.respond(final_response, false, nil, image_files)
end

bot.message(content: "!help") do |event|
  event.respond <<~EOS
    https://ob.sou7.io/simutrans/%E3%81%AA%E3%81%AA%E3%81%95%E3%81%B0/%E3%81%AA%E3%81%AA%E3%81%95%E3%81%B01%E6%9C%9F/nanasaba1st-map.png

    コマンド一覧
    - !help : このメッセージを表示します。
    - !chat : チャットします。「政場駅のスクリーンショット」と言うと、スクリーンショットを撮影します。

    管理用コマンド(特定チャンネル専用)
    - !overwrite : セーブデータを上書きします。
    - !restart : サーバーを再起動します。
  EOS
end

last_heartbeat = Time.now

bot.heartbeat() do |event|
  last_heartbeat = Time.now
end

bot.run true

loop do
  sleep 60
  if Time.now - last_heartbeat > 600
    puts "now : #{Time.now}"
    puts "last heartbeat : #{last_heartbeat}"
    bot.stop
    bot.run true
  end
end

