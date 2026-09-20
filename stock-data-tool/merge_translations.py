# -*- coding: utf-8 -*-
import json

with open("output/watchlist/dashboard_data.json", encoding="utf-8") as f:
    data = json.load(f)

TITLE_JA = {
 "ETF Oasis at Future Proof: Tuesday Highlights": "ETFオアシス(Future Proofカンファレンス):火曜日のハイライト",
 "S&P 500, Nasdaq, Dow End Higher As Drop In Oil Prices Allays Inflationary Concerns — NVDA, MCD, CRWV, LMT, AMZN In Focus": "原油価格下落でインフレ懸念が和らぎ、S&P500・ナスダック・ダウが上昇して引け ― NVDA、MCD、CRWV、LMT、AMZNに注目",
 "Fed Rate Hike in October or December? Benzinga Viewers Say This is More Likely": "FRBの利上げは10月か12月か? Benzinga読者調査ではこちらが有力",
 "Trump's Inflation Approval Slumps to 19%: What Do Prediction Markets Say About the Midterms?": "トランプ氏のインフレ対応支持率が19%に急落:予測市場は中間選挙をどう見ているか",
 "Gold price today, Thursday, September 17, 2026: Gold prices relatively stable following Fed rate increase": "本日の金価格(2026年9月17日木曜):FRB利上げ後も比較的安定",
 "Rocket Lab (RKLB) Completes $1.94 Billion Equity Offering": "ロケットラボ(RKLB)、19.4億ドルの株式売り出しを完了",
 "AngloGold Ashanti (AU) Surpasses Market Returns: Some Facts Worth Knowing": "アングロゴールド・アシャンティ(AU)、市場平均を上回るリターン:知っておきたい事実",
 "Agnico Eagle Mines (AEM) Outpaces Stock Market Gains: What You Should Know": "アグニコ・イーグル・マインズ(AEM)、市場平均を上回る上昇:知っておくべきこと",
 "When will mortgage rates go down? For now, rates are following the Fed": "住宅ローン金利はいつ下がるのか? 当面はFRBの動向次第",
 "Home contract signings drop 4.7% from last year amid higher mortgage rates": "住宅ローン金利上昇の中、中古住宅の仮契約件数は前年比4.7%減",
 "Dow Jones Futures Fall After S&P 500, Nasdaq Rebound Above Key Level; Moderna, AMD, SpaceX Flash Buy Signals": "S&P500とナスダックが節目水準を回復した後、ダウ先物は下落。モデルナ、AMD、スペースXに買いシグナル",

 "Qualcomm Just Rallied 18% in a Month: Take Profits, or Buy More?": "クアルコム、1カ月で18%急騰:利益確定か、それとも買い増しか",
 "3 Reasons SWKS is Risky and 1 Stock to Buy Instead": "SWKSがリスキーな3つの理由と、代わりに買うべき1銘柄",
 "1 Momentum  Stock with Competitive Advantages and 2 We Avoid": "競争優位を持つモメンタム株1銘柄と、避けるべき2銘柄",
 "Company News for Sep 16, 2026": "2026年9月16日の企業ニュース",
 "Qorvo (QRVO) Stock Looks Overvalued As Its 37% Rally Extends": "コーボ(QRVO)、37%上昇が続く中で割高感",
 "US Equity Markets End Lower as 10-Year Treasury Yield Climbs to Highest Since 2007, Oil Jumps": "米10年債利回りが2007年以来の高水準に上昇し原油も急騰、米国株は下落して引け",
 "Nvidia, Coinbase, Skyworks, Axon, Tesla, Applied Aerospace, and More Stocks That Explain Today’s Market": "エヌビディア、コインベース、スカイワークス、アクソン、テスラなど、本日の相場を象徴する銘柄",
 "Skyworks Solutions Stock Snaps Back From AI Selloff to Lead the S&P 500": "スカイワークス、AI関連売りから急反発しS&P500の上昇をけん引",

 "Marathon Petroleum (MPC) Exceeds Market Returns: Some Facts to Consider": "マラソン・ペトロリアム(MPC)、市場平均を上回るリターン:知っておきたい事実",
 "Think It’s Too Late to Buy Marathon and Valero? Here’s Why Analysts Say Wait Instead": "マラソンとバレロへの投資はもう遅い? アナリストが『待て』と言う理由",
 "Valero Energy Corporation (VLO) Hit a 52 Week High, Can the Run Continue?": "バレロ・エナジー(VLO)が52週高値を更新、上昇は続くか",
 "5 Relative Price Strength Stocks to Buy Amid Rising Rates": "金利上昇局面で買うべき『レラティブ・プライス・ストレングス』銘柄5選",
 "Bank of England holds rates at 3.75% as U.K. inflation hits 3.1%": "英インフレ率3.1%到達も、イングランド銀行は政策金利を3.75%に据え置き",
 "XOM Keeps Climbing. Should You Climb On?": "エクソンモービル(XOM)の上昇続く、乗るべきか",
 "This ETF Should Rise as Interest Rates Go Up. Is It Too Late to Get In on the Fun Now?": "金利上昇で恩恵を受けるはずのETF、今から乗るのは遅すぎるか",
 "Stocks to Watch Recap: UBS, Vera Bradley, Dave & Buster’s, Coinbase": "注目銘柄まとめ:UBS、ベラ・ブラッドリー、デーブ&バスターズ、コインベース",

 "Phillips 66: Resilient Refining Meets Midstream Stability": "フィリップス66:堅調な精製事業と安定したミッドストリーム事業",
 "Phillips 66 (PSX) Faces Bayway Labor Questions, Is The Stock Now Too Expensive?": "フィリップス66(PSX)、ベイウェイ製油所の労務問題に直面 ― 株価は割高か",
 "Phillips 66 (PSX) Rises As Market Takes a Dip: Key Facts": "市場が下落する中フィリップス66(PSX)は上昇:注目ポイント",
 "Sunoco Stock Breaks Out; Oil Prices Rise With No Clear End To Hormuz Closure": "スノコ株が上放れ、ホルムズ海峡封鎖の終息見通し立たず原油高が続く",
 "What Does the Future Hold for Valero Energy's Refining Business?": "バレロ・エナジーの精製事業の将来性は",
 "Global Fuel Squeeze Triggers U.S. Refiners Stocks Rally": "世界的な燃料需給逼迫で米精製株が上昇",
 "HF Sinclair Rises 113.9% in a Year: Should You Buy, Hold or Sell?": "HFシンクレア、1年で113.9%上昇 ― 買い・維持・売りどれを選ぶべきか",

 "Should You Buy HP Stock For The Shares It Keeps Retiring?": "HP株は自社株買いを理由に買うべきか",
 "Dell Gains Nearly 4% Today as 45-Watt Inference Expands Its Server Menu": "デル、45W推論対応でサーバー製品ラインナップ拡充し株価4%近く上昇",
 "Is Cisco Stock Priced For Orders That Are Not Yet Revenue?": "シスコ株はまだ売上に計上されていない受注を織り込みすぎか",
 "Lenovo, MemryX Partnership to Expand Sovereign Edge AI in Saudi Arabia": "レノボとメムリックスが提携、サウジアラビアでソブリン・エッジAIを拡大",
 "Dell’s AI Backlog Surge Positions Stock for $600+ as Server Revenue Doubles": "デル、AI受注残の急増でサーバー売上倍増、目標株価600ドル超えの声",
 "Did NetApp Borrow Its Record Quarter From The Rest Of The Year?": "ネットアップの好決算は今後の需要を『前借り』しただけか",
 "AI Server Stocks Rally as the Hardware Bid Broadens: Hewlett Packard Enterprise Jumps 9%, Super Micro Climbs 6%, Dell Rises 3%": "AIサーバー株が上昇、ハードウェア需要の広がりでHPEは9%急伸、スーパーマイクロは6%高、デルは3%高",
 "A $2.75 Billion Reason Why Micron Stock In Focus": "マイクロン株が注目される『27.5億ドル』の理由",

 "Salesforce CEO warns AI companies not to repeat this costly mistake": "セールスフォースCEO、AI企業に高くつく失敗を繰り返すなと警告",
 "Jim Cramer Prefers Palo Alto (PANW) Over SentinelOne (S)": "ジム・クレイマー氏、センチネルワン(S)よりパロアルトネットワークス(PANW)を選好",
 "Jim Cramer Highlights CrowdStrike (CRWD) as AI Security Concerns Lift Cybersecurity Stocks": "ジム・クレイマー氏、AIセキュリティへの懸念がサイバーセキュリティ株を押し上げる中クラウドストライク(CRWD)に注目",
 "2 Cybersecurity Stocks That Will Rule 2027": "2027年を制するサイバーセキュリティ銘柄2選",
 "Jim Cramer delivers unmistakable 2026 must-buy call on AI stock": "ジム・クレイマー氏、2026年『必買』のAI関連株を明確に推奨",
 "Semiconductor Stocks Just Tumbled. This Tech ETF Soared 6% Instead. Here's Why.": "半導体株が急落する中、このテックETFはなぜ6%急伸したのか",
 "Is CrowdStrike Holdings (CRWD) Priced For Perfection On Sales?": "クラウドストライク(CRWD)株は売上面で『完璧』を織り込みすぎか",
 "Okta Just Rallied 28% in a Month and Cybersecurity Stocks Are Red-Hot Now. Is $200 Coming Soon?": "オクタが1カ月で28%急騰、サイバーセキュリティ株が過熱気味 ― 200ドル到達は近いか",

 "Top Analyst Reports for Applied Materials, Philip Morris & Valero Energy": "アプライド・マテリアルズ、フィリップモリス、バレロ・エナジーの注目アナリストレポート",
 "Equinor Eyes LNG Expansion Amid Global Supply Disruptions": "エクイノール、世界的な供給混乱を背景にLNG事業拡大を検討",
 "Surging Earnings Estimates Signal Upside for Valero Energy (VLO) Stock": "業績予想の上方修正が相次ぎバレロ・エナジー(VLO)株の上昇を示唆",
 "Valero Energy (VLO) Rises As Market Takes a Dip: Key Facts": "市場が下落する中バレロ・エナジー(VLO)は上昇:注目ポイント",
 "Valero Energy (VLO) is a Great Momentum Stock: Should You Buy?": "バレロ・エナジー(VLO)は優良モメンタム株 ― 買うべきか",

 "Strength Seen in Revvity (RVTY): Can Its 9.1% Jump Turn into More Strength?": "レビティ(RVTY)に強さ ― 9.1%急伸はさらなる上昇につながるか",
 "Q2 Rundown: Revvity (NYSE:RVTY) Vs Other Research Tools & Consumables Stocks": "2Q総括:レビティ(RVTY)対他の研究ツール・消耗品銘柄",
 "3 Healthcare Stocks That Fall Short": "期待外れのヘルスケア株3選",
 "Revvity to Acquire Human Cell Design to Boost Metabolic Discovery": "レビティ、代謝研究強化のためヒューマン・セル・デザインを買収へ",
 "Is Revvity Stock a Buy as Growth Improves but Valuation Stays Rich?": "成長は改善もバリュエーションは高止まり ― レビティ株は買いか",
 "Revvity (RVTY) Stock Looks Fair On Cash Flow Yet Pricey On Earnings": "レビティ(RVTY)株、キャッシュフロー基準では妥当も利益基準では割高",
 "Revvity (RVTY) Margins Story Faces A Valuation Test Following Its Zacks Upgrade": "レビティ(RVTY)、Zacks格上げ後もマージン改善ストーリーがバリュエーションの試練に",
 "3 Hyped Up  Stocks We Find Risky": "過熱感のあるリスキーな銘柄3選",

 "SanDisk Stock Looks Cheap, But Can It Keep Earning This Much?": "サンディスク株は割安に見えるが、この高収益を維持できるか",
 "Can NetApp's Buccaneers Partnership Boost Its AI and Cloud Growth?": "ネットアップのバッカニアーズ提携はAI・クラウド成長を押し上げるか",
 "Are Computer and Technology Stocks Lagging  Hewlett Packard (HPE) This Year?": "今年、コンピューター・テクノロジー株はヒューレット・パッカード・エンタープライズ(HPE)に劣後しているか",
 "Did AI Servers Really Quadruple Dell Stock?": "AIサーバー需要はデル株を本当に4倍にしたのか",

 "2 Cash-Producing Stocks to Consider Right Now and 1 We Question": "今検討すべきキャッシュ創出力の高い銘柄2選と、疑問符が付く1銘柄",
 "1 S&P 500 Stock Worth Your Attention and 2 We Avoid": "注目に値するS&P500銘柄1選と、避けるべき2選",
 "Waters (WAT) Stock Could Be A Bargain On Cash Flow Yet Fully Priced On Sales": "ウォーターズ(WAT)株、キャッシュフロー基準では割安も売上高基準では適正価格",
 "Waters (WAT) Raised Guidance, Is The Stock Still Cheap?": "ウォーターズ(WAT)、通期見通しを上方修正 ― 株価はまだ割安か",
 "Leadership Shift And Upgraded Outlook Could Be A Game Changer For Waters (WAT)": "経営陣交代と見通し上方修正がウォーターズ(WAT)にとって転機に",
 "Why Is Waters (WAT) Up 3.1% Since Last Earnings Report?": "ウォーターズ(WAT)、前回決算以降なぜ3.1%上昇したのか",
 "Is Wall Street Bullish or Bearish on Waters Corporation Stock?": "ウォール街はウォーターズ・コーポレーション株に強気か弱気か",
 "Research Tools & Consumables Stocks Q2 Highlights: Waters Corporation (NYSE:WAT)": "研究ツール・消耗品セクター2Qハイライト:ウォーターズ・コーポレーション(NYSE:WAT)",

 "Top strategist thinks the Federal Reserve interest rate hike won't fix this huge earnings risk": "大手ストラテジスト、FRBの利上げでもこの巨大な業績リスクは解消しないと指摘",
 "What Makes HP (HPQ) a Strong Momentum Stock: Buy Now?": "HP(HPQ)が強いモメンタム株である理由 ― 今買うべきか",
 "What Happens To Apple Stock If Its Margin Keeps Slipping?": "マージン低下が続けばアップル株はどうなるか",
 "New Strong Buy Stocks for September 16th": "9月16日付の新規『強い買い』推奨銘柄",

 "Builders FirstSource (BLDR) Stock Falls Amid Market Uptick: What Investors Need to Know": "市場全体が上昇する中ビルダーズ・ファーストソース(BLDR)株は下落:投資家が知るべきこと",
 "Armstrong World Industries Makes Ceiling Tiles. Its Stock Is Anything but Boring.": "天井タイルのアームストロング・ワールド・インダストリーズ、株価は地味とは言えない値動き",
 "Owens Corning Stock Rises 17% in Six Months: Can the Upside Continue?": "オーウェンズ・コーニング株、半年で17%上昇 ― 上昇は続くか",
 "Builders FirstSource Stock: Is BLDR Underperforming the Industrials Sector?": "ビルダーズ・ファーストソース株:BLDRは資本財セクターに劣後しているか",
 "Is Lowe's Cheap Because Nobody Noticed Its Growth?": "ロウズ株が割安なのは成長性が見落とされているからか",
 "Three Stocks Are Joining the S&P 500. Will They Actually Improve VOO’s Returns?": "S&P500に新規採用の3銘柄、VOOのリターンを実際に改善するか",
 "Does Flat Sales And Rising Capital Intensity Change The Bull Case For Builders FirstSource (BLDR)?": "売上高の伸び悩みと設備投資負担の増加はビルダーズ・ファーストソース(BLDR)の強気材料を損なうか",
 "3 Out-of-Favor Stocks We’re Skeptical Of": "人気薄で懐疑的に見ている銘柄3選",

 "Is Rollins Stock Underperforming the Dow?": "ロリンズ株はダウ平均に劣後しているか",
 "5 Dividend Stocks Hiding in Boring Businesses Customers Cannot Live Without": "地味だが顧客に欠かせない事業に隠れた高配当株5選",
 "These 5 Boring Stocks Are Quietly Crushing the Market and Making Investors Rich": "地味な銘柄5選、静かに市場を圧倒し投資家を富ませる",
 "1 Mid-Cap Stock with Exciting Potential and 2 We Ignore": "有望な中型株1選と、見送るべき2選",
 "1 of Wall Street’s Favorite Stocks with Solid Fundamentals and 2 Facing Headwinds": "ウォール街お気に入りの堅調な銘柄1選と、逆風にさらされる2選",
 "2 Reasons to Like ROL and 1 to Stay Skeptical": "ROLを好感する理由2つと、懐疑的であるべき理由1つ",
 "1 Stock Under $50 to Consider Right Now and 2 We Question": "今検討すべき50ドル未満の銘柄1選と、疑問符が付く2選",
 "Why Is Rollins (ROL) Down 7.8% Since Last Earnings Report?": "ロリンズ(ROL)、前回決算以降なぜ7.8%下落したのか",

 "3 Reasons WYNN is Risky and 1 Stock to Buy Instead": "ウィン・リゾーツ(WYNN)がリスキーな3つの理由と、代わりに買うべき1銘柄",
 "Are Options Traders Betting on a Big Move in Wynn Resorts Stock?": "オプション取引者はウィン・リゾーツ株の大きな値動きに賭けているか",
 "Wynn Resorts Subsidiaries Launch $900 Million Private Offering of Senior Notes Due 2035": "ウィン・リゾーツ子会社、2035年満期の上級社債9億ドルの私募を実施",
 "3 Consumer Stocks We Steer Clear Of": "避けるべき消費関連株3選",
 "3 S&P 500 Stocks That Fall Short": "期待外れのS&P500銘柄3選",
 "Wynn Resorts (WYNN) Doubles Its Profit But Cracks Are Showing": "ウィン・リゾーツ(WYNN)、利益は倍増もほころびが見え始める",
 "Why Is Wynn (WYNN) Down 9.5% Since Last Earnings Report?": "ウィン(WYNN)、前回決算以降なぜ9.5%下落したのか",
 "Wynn Resorts (WYNN) Beat Expectations, Is The Stock Trading At A Discount?": "ウィン・リゾーツ(WYNN)は市場予想を上回ったが、株価は割安で取引されているか",

 "Is Las Vegas Sands Stock Underperforming the Nasdaq?": "ラスベガス・サンズ株はナスダックに劣後しているか",
 "MGM Stock Slips 14% in 3 Months: Is the Pullback a Buying Opportunity?": "MGM株、3カ月で14%下落 ― 押し目は買い場か",
 "Airlines, Cruises, Casinos: Are Things Actually Looking Up?": "航空・クルーズ・カジノ業界、本当に好転しているのか",
 "Las Vegas Sands (LVS) Down 0.1% Since Last Earnings Report: Can It Rebound?": "ラスベガス・サンズ(LVS)、前回決算以降0.1%下落 ― 反発はあるか",
 "Is Las Vegas Sands (LVS) Below Fair Value On Its Earnings Miss?": "決算未達のラスベガス・サンズ(LVS)は適正価値を下回っているか",
 "Monolithic Power Systems and Las Vegas Sands have been highlighted as Zacks Bull and Bear of the Day": "モノリシック・パワー・システムズとラスベガス・サンズがZacksの『本日の強気・弱気株』に選出",
 "Bear of the Day: Las Vegas Sands (LVS)": "本日の弱気株:ラスベガス・サンズ(LVS)",
 "WYNN's Q2 Beat Puts Macau Strength and Margin Pressure in Focus": "ウィンの2Q決算好調、マカオ事業の強さとマージン圧迫に注目集まる",

 "From Fashion to Concrete: J.P. Morgan Says Buy These 2 Stocks": "ファッションからコンクリートまで:JPモルガンが推奨する2銘柄",
 "How Is Martin Marietta Materials' Stock Performance Compared to Other Building Material Stocks?": "マーティン・マリエッタ・マテリアルズ株の値動きは他の建材銘柄と比べどうか",
 "1 S&P 500 Stock on Our Buy List and 2 Facing Challenges": "買いリストのS&P500銘柄1選と、課題に直面する2選",
 "Uber initiated, Thermo Fisher upgraded: Wall Street's top analyst calls": "ウーバーが新規カバレッジ、サーモフィッシャーが格上げ:ウォール街注目のアナリスト評価",
 "Here Are Tuesday’s Top Wall Street Analyst Research Calls: Abercrombie & Fitch, Affirm Holdings, Eagle Materials, Klarna Group, Martin Marietta Materials, Oklo, Qualcomm, Robinhood Markets, Ulta Beauty, and More": "火曜日の注目アナリストレポート:アバクロンビー&フィッチ、アファーム、イーグル・マテリアルズ、クラーナ、マーティン・マリエッタ、オクロ、クアルコム、ロビンフッド、ウルタ・ビューティーなど",
 "Chip, Drug Makers to Drive Non-Residential Construction Rebound, UBS Says": "半導体・製薬企業の投資が非住宅建設の回復をけん引とUBS",
 "Andvari Associates Strategic Investment in Martin Marietta Materials (MLM)": "アンドヴァリ・アソシエイツ、マーティン・マリエッタ・マテリアルズ(MLM)に戦略的投資",

 "NRG Energy (NRG) Stock Sinks As Market Gains: Here's Why": "市場全体が上昇する中NRGエナジー(NRG)株は下落:その理由",
 "The Nuclear Stock Boom Could Keep Decaying": "原子力関連株ブームはなお冷え込みが続く可能性",
 "Clearway Energy (CWEN) Dips More Than Broader Market: What You Should Know": "クリアウェイ・エナジー(CWEN)、市場平均以上に下落:知っておくべきこと",
 "Vistra’s Price Has Edged Downward Throught 2026: One Analyst Says It’s Due to Double Soon.": "ビストラ株、2026年を通じて軟調 ― あるアナリストは近く倍増すると予測",
 "NRG Energy (NRG) Laps the Stock Market: Here's Why": "NRGエナジー(NRG)、市場平均を上回る:その理由",
 "Can CEG's Expanding Generation Portfolio Drive Long-Term Growth?": "コンステレーション・エナジーの発電ポートフォリオ拡大は長期成長をけん引するか",
 "NRG Energy, Inc. (NRG) is Attracting Investor Attention: Here is What You Should Know": "NRGエナジー(NRG)、投資家の注目を集める:知っておくべきこと",
 "Should You Buy Vistra Stock For Its Shrinking Share Count?": "自社株買いで発行済み株式数が減少するビストラ株は買いか",

 "Why Has McDonald's Gone Quiet On Its Low-Income Customer?": "マクドナルドはなぜ低所得層顧客について沈黙しているのか",
 "MCD Stock Fades After 0.7% Pop On Value-Menu Revamp Report": "バリューメニュー刷新報道で0.7%上昇したMCD株、その後失速",
 "McDonald’s said to plan value strategy overhaul to revive US sales growth": "マクドナルド、米国売上高回復に向け値ごろ感戦略の刷新を計画と報道",
 "McDonald’s CEO Admits Execution Failure as K-Shape Economy Splits Consumer Base": "K字型景気で消費者層が二極化する中、マクドナルドCEOが実行面の失敗を認める",
 "One of These 3 Companies Is One Year From Becoming a Dividend King. Here Is Which One": "この3社のうち1社は1年後に『配当王』の仲間入り ― それはどこか",
 "Chili’s Gearing Up for Battle With Taco Bell": "チリズ、タコベルとの競争に備える",
 "BROS Trades at 38.45X P/E: Should Investors Buy, Sell or Hold?": "PER38.45倍で取引されるBROS ― 投資家は買い・売り・維持どれを選ぶべきか",
 "Can Starbucks' 600-650 New Stores Strengthen Its Global Growth?": "スターバックスの新規600~650店舗出店計画は世界的成長を強化するか",

 "CRH (CRH) Suffers a Larger Drop Than the General Market: Key Insights": "CRH(CRH)、市場全体以上に下落:主な注目点",
 "Here's Why CRH (CRH) Fell More Than Broader Market": "CRH(CRH)が市場平均以上に下落した理由",
 "Arcosa Shareholders Approve $8.5B CRH Deal. Does the Vote De-Risk a First-Quarter 2027 Closing?": "アルコサ株主、CRHとの85億ドル取引を承認 ― 2027年1-3月期のクロージングへのリスクは後退したか",
 "2 ‘Perfect 10’ Stocks Wall Street Is Betting On": "ウォール街が賭ける『パーフェクト10』銘柄2選",
 "Dycom Q2 Earnings & Revenues Top Estimates on Strong Fiber Demand": "ダイコム、光ファイバー需要の強さで2Q決算は増益増収",
 "Dycom to Report Q2 Earnings: Here's What to Expect This Season": "ダイコム、2Q決算発表控える ― 今期の注目点",
 "Toll Brothers Beats Q3 Earnings & Revenue Estimates on Higher Pricing": "トール・ブラザーズ、価格上昇で3Q決算は市場予想を上回る増収増益",

 "Why your cell phone bill is getting so expensive — and how that helped convince the Fed to raise rates": "携帯電話料金がこれほど高くなっている理由 ― それがFRBの利上げ判断を後押しした経緯",
 "Apple iPhone 18 Pro Sales Helped By Carrier Promotions": "アップルのiPhone 18 Pro販売、通信キャリアの販促が後押し",
 "Apple's iPhone 18 lineup keeps Bank of America bullish": "アップルのiPhone 18ラインナップ、バンク・オブ・アメリカは強気維持",
 "T-Mobile adds monthly fee to a new iPhone feature for customers": "Tモバイル、新しいiPhone機能に月額料金を設定",
 "Renewed Industry Competition Sparks T-Mobile US’s (TMUS) Sell-Off": "業界内競争の再燃でTモバイルUS(TMUS)株が売られる",
 "US official says upcoming spectrum auctions could generate more than $100 billion": "米当局者、今後の周波数オークションは1000億ドル超の収入をもたらす可能性と発言",
 "T Mobile US (TMUS) Sets Up A Long Term CFO Succession Plan": "Tモバイル US(TMUS)、長期的なCFO承継計画を策定",
 "What Does AT&T Stock Do To Your Money When The Market Falls?": "市場下落時、AT&T株はあなたの資産をどう守るか",

 "TD Bank Targets 100 U.S. Branches as AML Remediation Continues": "TDバンク、マネロン対策の是正が続く中で米国内100店舗展開を目指す",
 "Boeing (BA) Stock Sinks As Market Gains: What You Should Know": "市場全体が上昇する中ボーイング(BA)株は下落:知っておくべきこと",
 "“Delayed Isn’t as Good”: Why Boeing’s $10 Billion Cash Flow Target Just Got More Expensive": "『遅延は好ましくない』― ボーイングの100億ドルのキャッシュフロー目標達成コストが上昇した理由",
 "Boeing (BA)’s $8.4 Billion Supplier Buyback Keeps Turning Up New Costs": "ボーイング(BA)の84億ドル規模のサプライヤー買い戻し、新たなコストが次々判明",
 "Boeing CEO Kelly Ortberg warns 737 Max production ramp is delayed": "ボーイングのオートバーグCEO、737MAXの増産計画の遅れを警告",
 "Update: Market Chatter: US, Vietnam Firms Set to Announce Deals During To Lam Visit": "続報:トー・ラム氏訪米に合わせ米越企業が契約発表へとの市場観測",
 "Boeing (BA) Lands Up To Four Freighter Orders And A New Cargo Lease": "ボーイング(BA)、貨物機最大4機の受注と新たなカーゴリース契約を獲得",
 "Jim Cramer Sees Boeing (BA) Rising If Oil Peaks": "ジム・クレイマー氏、原油価格がピークを付ければボーイング(BA)は上昇すると見方",
}

NAME_JA = {
 "Skyworks Solutions": "スカイワークス・ソリューションズ",
 "Marathon Petroleum": "マラソン・ペトロリアム",
 "Phillips 66": "フィリップス66",
 "Dell Technologies": "デル・テクノロジーズ",
 "CrowdStrike": "クラウドストライク",
 "Valero Energy": "バレロ・エナジー",
 "Revvity": "レビティ",
 "Hewlett Packard Enterprise": "ヒューレット・パッカード・エンタープライズ",
 "Waters Corporation": "ウォーターズ・コーポレーション",
 "HP Inc.": "HP",
 "Builders FirstSource": "ビルダーズ・ファーストソース",
 "Rollins, Inc.": "ロリンズ",
 "Wynn Resorts": "ウィン・リゾーツ",
 "Las Vegas Sands": "ラスベガス・サンズ",
 "Martin Marietta Materials": "マーティン・マリエッタ・マテリアルズ",
 "NRG Energy": "NRGエナジー",
 "McDonald's": "マクドナルド",
 "CRH plc": "CRH",
 "T-Mobile US": "Tモバイル US",
 "Boeing": "ボーイング",
}

def tmpl_reason(label):
    return {
        "強気（上昇優勢）": "主要移動平均線・トレンド指標が明確な上昇シグナル",
        "やや強気": "MACD・株価位置はプラスだがモメンタムはやや控えめ",
        "中立": "指標が強弱まちまちで方向感に乏しい",
        "やや弱気": "移動平均線を下回るなど弱含みの兆候",
        "弱気（下落優勢）": "主要移動平均線・トレンド指標が明確な下降シグナル",
    }[label]

# ticker -> fundamental judgment (label, reason)
FUNDAMENTAL = {
 # JP bullish
 "5301.T": ("中立", "自己株式消却や決算関連の開示が中心で重大な材料なし"),
 "9433.T": ("中立", "自己株式取得や決算開示が中心で重大な材料なし"),
 "6178.T": ("中立", "決算・自己株式関連の開示が中心で重大な材料なし"),
 "8766.T": ("やや強気", "株式分割・株主優待制度導入など株主還元強化の動き"),
 "9434.T": ("やや強気", "T&Dフィナンシャル生命保険の子会社化など事業拡大の動き"),
 "8001.T": ("やや強気", "電通総研へのTOB開始など積極的なM&A・株主還元の動き"),
 "2871.T": ("やや弱気", "グループでのシステム障害発生が2度開示され、業務への影響が懸念材料"),
 "1721.T": ("中立", "自己株式取得や決算関連の開示が中心で重大な材料なし"),
 "9432.T": ("中立", "自己株式取得や決算開示が中心で重大な材料なし"),
 "5020.T": ("やや強気", "TPC Holdings, Inc.の買収など事業拡大の動き"),
 # JP bearish
 "7532.T": ("やや弱気", "代表取締役の異動や上場廃止子会社の整理に関する開示が続き経営面での不透明感"),
 "4755.T": ("弱気（下落優勢）", "減損損失の計上を開示するなど収益悪化を示唆する材料"),
 "7741.T": ("中立", "内視鏡事業の戦略的オプション検討など事業再編の動きはあるが方向性は不透明"),
 "5706.T": ("中立", "株式分割等はあるが業績に直結する重大な材料は見当たらない"),
 "6146.T": ("やや弱気", "1Q業績が事前予想値と乖離したとの開示があり、需要動向への警戒感"),
 "4519.T": ("中立", "決算関連の定例開示が中心で重大な材料なし"),
 "4151.T": ("中立", "決算関連の定例開示が中心で重大な材料なし"),
 "7731.T": ("やや弱気", "精機事業で減損損失・棚卸資産評価損の計上を開示"),
 "8267.T": ("やや弱気", "熊本地震の影響やイオンモール熊本の爆発事故など営業への逆風"),
 "8804.T": ("中立", "決算関連の定例開示が中心で重大な材料なし"),
 # US bullish
 "SWKS": ("中立", "AI関連売りからの反発観測と株価の割高感を指摘する声が拮抗"),
 "MPC": ("やや強気", "市場平均を上回るリターンと精製マージン改善への強気見通し"),
 "PSX": ("やや強気", "原油供給懸念による精製マージン改善期待の一方、労務問題や割高感も指摘"),
 "DELL": ("強気（上昇優勢）", "AIサーバー需要の拡大でバックログが急増し目標株価引き上げの見方"),
 "CRWD": ("やや強気", "AIセキュリティ需要の高まりでサイバーセキュリティ株全般に追い風、一方で高バリュエーションへの懸念も"),
 "VLO": ("強気（上昇優勢）", "業績予想の上方修正が相次ぎ52週高値を更新するなど強い上昇モメンタム"),
 "RVTY": ("やや強気", "代謝研究分野の買収など成長期待がある一方、バリュエーションの高さへの懸念も"),
 "HPE": ("強気（上昇優勢）", "AIサーバー需要拡大を背景に株価が9%急伸するなど強い上昇基調"),
 "WAT": ("やや強気", "業績見通しの上方修正と経営陣刷新が好感される一方、バリュエーション面はやや割高"),
 "HPQ": ("やや強気", "自社株買いの継続とモメンタム株としての評価が支え"),
 # US bearish
 "BLDR": ("弱気（下落優勢）", "住宅建設需要の鈍化を背景に売上高伸び悩みと設備投資負担増加が懸念材料"),
 "ROL": ("やや弱気", "決算後に株価が下落しており、成長鈍化への懸念がくすぶる"),
 "WYNN": ("やや弱気", "増益ながら『ほころび』が指摘され、大型社債発行による財務負担も懸念"),
 "LVS": ("弱気（下落優勢）", "決算未達やマカオ事業のマージン圧迫でZacks『Bear of the Day』に選定"),
 "MLM": ("中立", "非住宅建設の回復期待や投資家の買い増しがある一方、直近の株価は軟調"),
 "NRG": ("やや弱気", "原子力関連銘柄への過熱感後退で株価が軟調"),
 "MCD": ("弱気（下落優勢）", "CEOが低価格帯戦略の実行不足を認め、売上てこ入れへの戦略見直しを迫られている"),
 "CRH": ("中立", "Arcosa買収承認など前向き材料もあるが、直近株価は市場平均に劣後"),
 "TMUS": ("弱気（下落優勢）", "業界内の競争激化により大幅な株安を招いている"),
 "BA": ("やや弱気", "737MAXの増産計画遅延とコスト増加への懸念が重荷"),
}

def process_stock(s):
    ticker = s["ticker"]
    if not ticker.endswith(".T"):
        name_ja = NAME_JA.get(s["name"])
        if name_ja:
            s["name_ja"] = name_ja
    if s.get("fundamentals_source") == "Yahoo Finance News":
        for h in (s.get("fundamentals_raw") or []):
            t = h.get("title")
            if t in TITLE_JA:
                h["title_ja"] = TITLE_JA[t]
    combined = s["combined"]
    f_label, f_reason = FUNDAMENTAL[ticker]
    s["claude_judgment"] = {
        "short": {"label": combined["short_term"]["label"], "reason": tmpl_reason(combined["short_term"]["label"])},
        "mid": {"label": combined["mid_term"]["label"], "reason": tmpl_reason(combined["mid_term"]["label"])},
        "long": {"label": combined["long_term"]["label"], "reason": tmpl_reason(combined["long_term"]["label"])},
        "fundamental": {"label": f_label, "reason": f_reason},
    }

for mkey, mval in data["markets"].items():
    for cat, stocks in mval.items():
        for s in stocks:
            process_stock(s)

for item in data.get("macro_news", []):
    t = item.get("title")
    if t in TITLE_JA:
        item["title_ja"] = TITLE_JA[t]

with open("output/watchlist/dashboard_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)

print("merged OK")

# sanity check: all judgments filled
missing = []
for mkey, mval in data["markets"].items():
    for cat, stocks in mval.items():
        for s in stocks:
            if s.get("claude_judgment") is None:
                missing.append(s["ticker"])
print("missing judgments:", missing)
