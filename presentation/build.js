// Echo final-project deck: 8 slides, numbers from eval/report.md and cost/budget.py (run 5, 20.11.2026).
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.PPTX_SKILL + "/scripts/apply_theme.js");

const OUT = path.join(__dirname, "..", "submission", "Эхо_презентация.pptx");
const SHOTS = path.join(__dirname, "shots");

const THEME = {
  name: "Lavka Tepla",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "2B2118", lt1: "FFFFFF", dk2: "8C3B2E", lt2: "F5EEE6",
    accent1: "B85042", accent2: "6F8F7E", accent3: "D9A441", accent4: "6B4F3F", accent5: "E7D9C8", accent6: "3E6259",
    hlink: "B85042", folHlink: "6B4F3F",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.title = "Эхо: ассистент поддержки по отзывам";
pres.author = "Студент курса «Промпт-инжиниринг 3.0»";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;
const W = 13.333;

pres.defineSlideMaster({
  title: "DARK",
  background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.7, y: 1.2, w: 11.9, h: 1.3, fontSize: 40, bold: true,
      color: C.background1, fontFace: THEME.headFontFace, valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background2 },
  margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.9, fontSize: 30, bold: true,
      color: C.text1, fontFace: THEME.headFontFace, valign: "middle", margin: 0 }, text: "" } },
    { text: { text: "Эхо · выпускной проект · Промпт-инжиниринг 3.0", options: { x: 0.6, y: 7.0, w: 8, h: 0.3, fontSize: 10,
      color: C.accent4, margin: 0 } } },
  ],
  slideNumber: { x: 12.3, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: C.accent4, align: "right" },
});

// ---------- helpers ----------
let objN = 0;
const name = (s) => `${s}-${++objN}`;
function card(slide, x, y, w, h, fill = C.background1) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: fill },
    line: { color: C.accent5, width: 1 }, objectName: name("card") });
}
function text(slide, t, opts) {
  slide.addText(t, { isTextBox: true, margin: 0, valign: "top", fontSize: 14, color: C.text1, objectName: name("text"), ...opts });
}
function stat(slide, x, y, w, big, label, bigColor = C.accent1) {
  text(slide, big, { x, y, w, h: 0.9, fontSize: 32, bold: true, color: bigColor, fontFace: THEME.headFontFace });
  text(slide, label, { x, y: y + 0.95, w, h: 0.9, fontSize: 13, color: C.accent4 });
}
function dot(slide, x, y, n, fill = C.accent1) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: 0.5, h: 0.5, fill: { color: fill }, line: { color: fill, width: 0 },
    objectName: name("dot") });
  text(slide, String(n), { x, y, w: 0.5, h: 0.5, fontSize: 16, bold: true, color: C.background1, align: "center", valign: "middle" });
}

// ---------- 1. Problem ----------
pres.addSection({ title: "Проблема" });
let s = pres.addSlide({ masterName: "DARK", sectionTitle: "Проблема" });
text(s, "ВЫПУСКНОЙ ПРОЕКТ · ПРОМПТ-ИНЖИНИРИНГ 3.0", { x: 0.7, y: 0.6, w: 10, h: 0.4, fontSize: 13, bold: true, color: C.accent3, charSpacing: 2 });
s.addText("Эхо: ассистент поддержки по отзывам", { placeholder: "title" });
text(s, "Учебный магазин товаров для дома «Лавка Тепла». Поддержка из 2 человек читает каждый отзыв, а жалобы "
  + "на брак тонут среди благодарностей.", { x: 0.7, y: 2.45, w: 11.5, h: 0.9, fontSize: 18, color: C.accent5 });
const probs = [
  ["3 часа", "в день поддержка тратит на чтение отзывов и ответы с нуля"],
  ["40–60", "отзывов в день, до 150 в сезон распродаж"],
  ["1–2 дня", "может ждать ответа срочная жалоба: клиент пишет повторный негатив, падает рейтинг карточки"],
];
probs.forEach(([big, label], i) => {
  const x = 0.7 + i * 4.1;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 3.9, w: 3.8, h: 2.5, rectRadius: 0.12, fill: { color: C.text2 },
    line: { color: C.text2, width: 0 }, objectName: name("problem") });
  text(s, big, { x: x + 0.3, y: 4.15, w: 3.2, h: 0.9, fontSize: 44, bold: true, color: C.background1, fontFace: THEME.headFontFace });
  text(s, label, { x: x + 0.3, y: 5.1, w: 3.2, h: 1.2, fontSize: 15, color: C.accent5 });
});
s.addNotes("Проблема из ТЗ, раздел 1.2. Ответы пишутся разными словами, повторяющиеся проблемы замечают через месяц. "
  + "Правилами по ключевым словам отзыв не разобрать: «всё отлично, только ручка отвалилась» это жалоба.");

// ---------- 2. Solution ----------
pres.addSection({ title: "Решение" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Решение" });
s.addText("Решение: разбор и черновик за 6 секунд", { placeholder: "title" });
const funcs = [
  ["Размечает отзыв", "Тональность, тип, темы, срочность и отдел строго по справочнику магазина (документ 07)."],
  ["Пишет черновик", "В тоне магазина, на шаблоне нужного типа, с фактами из базы: сроки, адрес почты, порядок при браке."],
  ["Показывает источники", "Ссылка на документ и раздел базы, из которых взят каждый факт. Клик открывает раздел."],
  ["Не выдумывает", "Нет факта в базе: метка [уточнить у отдела]. Деньги и скидки: метка [решение менеджера]."],
];
funcs.forEach(([h, b], i) => {
  const x = 0.6 + (i % 2) * 6.15, y = 1.55 + Math.floor(i / 2) * 2.6;
  card(s, x, y, 5.95, 2.35);
  dot(s, x + 0.35, y + 0.35, i + 1, i === 3 ? C.accent2 : C.accent1);
  text(s, h, { x: x + 1.1, y: y + 0.35, w: 4.6, h: 0.5, fontSize: 20, bold: true, fontFace: THEME.headFontFace, valign: "middle" });
  text(s, b, { x: x + 1.1, y: y + 1.0, w: 4.6, h: 1.2, fontSize: 15, color: C.accent4 });
});
s.addNotes("Сотрудник вставляет отзыв или свой вопрос. Публикует ответ всегда человек: ассистент с клиентами не общается.");

// ---------- 3. How it works ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Решение" });
s.addText("Как работает: поиск по базе знаний, потом модель", { placeholder: "title" });
const steps = [
  ["Отзыв или вопрос", "Сотрудник вставляет текст, площадку и оценку в веб-форму"],
  ["Поиск по базе", "FAISS по 16 документам: 4 фрагмента с фактами и 2 шаблона ответа"],
  ["Claude Haiku 4.5", "Промпт и 4 постоянных документа из кэша на 1 час, ответ по JSON-схеме"],
  ["Разбор и черновик", "Разметка, черновик, заметка для команды, ссылки на источники"],
];
steps.forEach(([h, b], i) => {
  const x = 0.6 + i * 3.15;
  card(s, x, 1.7, 2.75, 2.6, i === 2 ? C.lt2 : C.background1);
  dot(s, x + 0.25, 1.95, i + 1);
  text(s, h, { x: x + 0.25, y: 2.6, w: 2.35, h: 0.5, fontSize: 16, bold: true, fontFace: THEME.headFontFace });
  text(s, b, { x: x + 0.25, y: 3.15, w: 2.3, h: 1.1, fontSize: 13, color: C.accent4 });
  if (i < 3) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + 2.8, y: 2.8, w: 0.3, h: 0.4, fill: { color: C.accent1 },
    line: { color: C.accent1, width: 0 }, objectName: name("arrow") });
});
card(s, 0.6, 4.65, 12.1, 2.05, C.background1);
text(s, "Почему так", { x: 0.9, y: 4.85, w: 4, h: 0.4, fontSize: 16, bold: true, fontFace: THEME.headFontFace });
text(s, [
  { text: "База выросла с 10 до 16 документов: целиком это ≈ 21 000 токенов на каждый запрос.", options: { bullet: true, breakLine: true } },
  { text: "Шаблоны похожи на отзывы и вытесняли справки, поэтому у них свои 2 места в выдаче.", options: { bullet: true, breakLine: true } },
  { text: "Порядок при браке, справочник, маршрутизация и особые случаи нужны почти всегда: идут целиком и кэшируются.", options: { bullet: true } },
], { x: 0.9, y: 5.3, w: 11.5, h: 1.3, fontSize: 14, color: C.accent4, paraSpaceAfter: 4 });
s.addNotes("Стек MVP: Python, LangChain, FAISS, эмбеддинги text-embedding-3-small и модель через OpenRouter, интерфейс Streamlit. "
  + "В боевой версии вместо формы Telegram-бот через n8n.");

// ---------- 4. Demo: typical ----------
pres.addSection({ title: "Демо" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Демо" });
s.addText("Демо: 5 типовых вопросов", { placeholder: "title" });
const typical = [
  ["Плед полинял после стирки на 30°", "жалоба, высокая, контроль качества; порядок при браке из базы"],
  ["Как стирать подушку «Сон»?", "вопрос сотрудника: 40°, отжим до 600, сушить расправленной"],
  ["Курьер позвонил заранее, кружки целые", "благодарность, 21 слово, курьеру передадут спасибо"],
  ["Бельё хорошее, но доставка шла 9 дней", "смешанный: спасибо за товар, срок 3–7 дней из базы"],
  ["Кружка с трещиной, телефон в отзыве (WB)", "склад и доставка; телефон и номер заказа в ответ не попали"],
];
typical.forEach(([q, a], i) => {
  const y = 1.5 + i * 1.07;
  dot(s, 0.6, y + 0.05, i + 1);
  text(s, q, { x: 1.3, y, w: 5.2, h: 0.4, fontSize: 15, bold: true });
  text(s, a, { x: 1.3, y: y + 0.42, w: 5.2, h: 0.55, fontSize: 13, color: C.accent4 });
});
s.addImage({ path: path.join(SHOTS, "01_defect.jpg"), x: 6.85, y: 1.5, w: 5.85, h: 5.85 * 562 / 800,
  altText: "Интерфейс Эхо: разбор жалобы на плед, черновик ответа и четыре источника из базы знаний", objectName: name("shot") });
text(s, "Разбор жалобы на плед в интерфейсе: разметка, черновик, источники, 8 850 токенов из кэша",
  { x: 6.85, y: 5.75, w: 5.85, h: 0.5, fontSize: 11, italic: true, color: C.accent4 });
s.addNotes("Все 7 демо-вопросов есть кнопками в интерфейсе. Ответы взяты из итогового прогона 5 и локального запуска 20.11.2026.");

// ---------- 5. Demo: out of KB ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Демо" });
s.addText("Демо: 2 вопроса вне базы", { placeholder: "title" });
const offk = [
  ["Клиент из Алматы: доставляете ли в Казахстан и сколько стоит?",
   "«Ответить, что уточним возможность доставки в Казахстан и стоимость, попросить написать на почту поддержки. "
   + "Метка [уточнить у отдела]».", "Правила «не доставляем» и сроков не придумал. Источник: документ 02, раздел «Чего в базе нет»."],
  ["Заказ опоздал на 4 дня: «требую 1 000 рублей, иначе Роспотребнадзор»",
   "«…Ваш запрос о компенсации передали руководителю поддержки: [решение менеджера]…»",
   "Денег не обещает, отдел из базы. В PEf03 здесь появлялся несуществующий юротдел."],
];
offk.forEach(([q, a, why], i) => {
  const y = 1.5 + i * 2.75;
  card(s, 0.6, y, 6.6, 2.5);
  text(s, q, { x: 0.9, y: y + 0.2, w: 6.0, h: 0.7, fontSize: 15, bold: true });
  text(s, a, { x: 0.9, y: y + 0.95, w: 6.0, h: 0.8, fontSize: 13, italic: true, color: C.text2 });
  text(s, why, { x: 0.9, y: y + 1.75, w: 6.0, h: 0.65, fontSize: 12, color: C.accent4 });
});
s.addImage({ path: path.join(SHOTS, "03_doc_link.jpg"), x: 7.5, y: 1.5, w: 5.2, h: 5.2 * 562 / 800,
  altText: "Страница базы знаний: открыт документ 02, подсвечен раздел, на который сослался ассистент", objectName: name("shot") });
text(s, "Ссылка из ответа открывает документ 02 и подсвечивает раздел, на который сослался ассистент",
  { x: 7.5, y: 5.25, w: 5.2, h: 0.6, fontSize: 11, italic: true, color: C.accent4 });
s.addNotes("При ручной проверке в интерфейсе модель один раз назвала срок ответа «1–2 рабочих дня», которого нет в базе. "
  + "В промпт добавлен запрет на сроки не из фрагментов, после этого сроков не из базы нет ни в одном из 15 ответов.");

// ---------- 6. Results ----------
pres.addSection({ title: "Результаты" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Результаты" });
s.addText("Результаты на 15 тестовых входах", { placeholder: "title" });
stat(s, 0.6, 1.45, 2.9, "15 из 15", "поиск нашёл нужный документ (цель ≥ 14)");
stat(s, 3.65, 1.45, 2.9, "12 / 3 / 0", "ответов верно / частично / неверно");
stat(s, 6.7, 1.45, 2.9, "0", "выдуманных фактов и обещаний денег", C.accent2);
stat(s, 9.75, 1.45, 2.9, "5,6 с", "медиана ответа, максимум 7,5 с (цель < 10 с)");
const hdr = { bold: true, color: C.background1, fill: { color: C.accent1 }, fontSize: 13 };
const cell = (t, o = {}) => ({ text: t, options: { fontSize: 13, color: C.text1, ...o } });
s.addTable([
  [{ text: "Показатель", options: hdr }, { text: "PEf03: вся база в промпте", options: hdr }, { text: "MVP: поиск + кэш", options: hdr }],
  [cell("Ответов верно / частично / неверно"), cell("5 / 4 / 1 (из 10)"), cell("12 / 3 / 0 (из 15)", { bold: true })],
  [cell("Выдуманные факты"), cell("правило о доставке, юротдел"), cell("нет", { bold: true })],
  [cell("Ссылки на источники"), cell("не было"), cell("13 из 15 ответов")],
  [cell("Стоимость запроса"), cell("$0,011"), cell("$0,0041", { bold: true })],
], { x: 0.6, y: 3.55, w: 7.4, colW: [2.9, 2.25, 2.25], rowH: 0.42, border: { type: "solid", pt: 0.75, color: HEX.accent5 },
  fill: { color: C.background1 }, valign: "middle", objectName: name("results") });
card(s, 8.35, 3.55, 4.35, 2.95);
text(s, "Что не дотянули", { x: 8.65, y: 3.75, w: 3.8, h: 0.4, fontSize: 16, bold: true, fontFace: THEME.headFontFace });
text(s, [
  { text: "2 ответа без ссылок на источники", options: { bullet: true, breakLine: true } },
  { text: "1 ответ пишет клиенту «в базе нет информации» вместо метки", options: { bullet: true, breakLine: true } },
  { text: "Поиск настраивался на этих же 15 входах: нужен эталон из 50 новых отзывов", options: { bullet: true } },
], { x: 8.65, y: 4.25, w: 3.8, h: 2.1, fontSize: 13, color: C.accent4, paraSpaceAfter: 6 });
s.addNotes("Пять прогонов эталона: два на правки промпта, один с кэшем, два на правки после ручной проверки. "
  + "Haiku 5.5 на том же наборе: 8 / 6 / 1, поэтому оставлена Haiku 4.5.");

// ---------- 7. Cost ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Результаты" });
s.addText("Стоимость: в лимит 1 500 ₽ на API благодаря кэшу", { placeholder: "title" });
s.addChart(pres.charts.BAR, [{ name: "API, ₽ в месяц", labels: ["Вся база в промпте", "Поиск без кэша", "Поиск + кэш (выбран)", "Haiku 5.5"],
  values: [2084, 2219, 918, 222] }], {
  x: 0.6, y: 1.45, w: 6.6, h: 4.9, barDir: "bar", chartColors: [HEX.accent5, HEX.accent5, HEX.accent1, HEX.accent5],
  showTitle: true, title: "API в месяц, ₽ (1 980 запросов)", titleFontSize: 14, titleColor: HEX.dk1, titleFontFace: "+mn-lt",
  showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 12, dataLabelColor: HEX.dk1, dataLabelFormatCode: "# ##0",
  catAxisLabelColor: HEX.accent4, catAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt", catAxisOrientation: "maxMin",
  valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false,
  dataLabelFontFace: "+mn-lt", objectName: name("cost-chart"),
});
stat(s, 7.5, 1.45, 2.5, "$0,0041", "за запрос с кэшем (без кэша $0,0118)");
stat(s, 10.2, 1.45, 2.5, "9 383 ₽", "в месяц на магазин: API, сервер, поддержка, буфер 30%");
stat(s, 7.5, 3.4, 2.5, "10,7 мес", "окупаемость разработки (93 000 ₽) за счёт 2 ч экономии в день");
stat(s, 10.2, 3.4, 2.5, "4 клиента", "безубыточность, если продавать как сервис за 7 990 ₽ в месяц");
text(s, "Haiku 5.5 дешевле ещё в 4 раза, но ошибается вдвое чаще: путает похвалу с жалобой, называет клиента чужим именем.",
  { x: 7.5, y: 5.45, w: 5.2, h: 0.9, fontSize: 13, italic: true, color: C.accent4 });
s.addNotes("Расчёт в файле Эхо_бюджет_и_монетизация.xlsx. Курс 90 ₽ за доллар, ставка 1 500 ₽ в час, 4 записи кэша в день.");

// ---------- 8. Plans ----------
pres.addSection({ title: "Планы" });
s = pres.addSlide({ masterName: "DARK", sectionTitle: "Планы" });
s.addText("Планы", { placeholder: "title" });
const plans = [
  ["Telegram-бот", "Команда работает в Telegram: бот через n8n, журнал разборов, уведомление о срочной жалобе"],
  ["Проверки кодом", "Ловить сроки не из базы, фразу «в базе нет» и пропущенную метку до того, как черновик увидит сотрудник"],
  ["Эталон из 50 отзывов", "Реальные отзывы, которые не участвовали в настройке поиска; пилот с 1 сотрудником"],
  ["Дальше", "Отзывы с Ozon и Wildberries по API, недельная сводка, подписка для других магазинов"],
];
plans.forEach(([h, b], i) => {
  const x = 0.7 + (i % 2) * 6.1, y = 2.5 + Math.floor(i / 2) * 2.2;
  dot(s, x, y + 0.05, i + 1, C.accent3);
  text(s, h, { x: x + 0.75, y, w: 5.0, h: 0.5, fontSize: 20, bold: true, color: C.background1, fontFace: THEME.headFontFace });
  text(s, b, { x: x + 0.75, y: y + 0.6, w: 5.0, h: 1.3, fontSize: 15, color: C.accent5 });
});
s.addNotes("Код, база знаний, отчёт о проверке и ТЗ v1.1 приложены к работе.");

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("saved", OUT);
})();
