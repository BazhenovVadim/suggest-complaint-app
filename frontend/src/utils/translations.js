export const STATUS_TRANSLATIONS = {
  NEW: "Новое",
  IN_PROGRESS: "В обработке",
  RESOLVED: "Решено",
  REJECTED: "Отклонено",
};

export const TYPE_TRANSLATIONS = {
  COMPLAINT: "Жалоба",
  SUGGESTION: "Предложение",
  QUESTION: "Вопрос",
  REQUEST: "Запрос",
};

export const LOCATION_TRANSLATIONS = {
  STUDENT_CAMPUS: "Студгородок",
  DORMITORY: "Общежитие",
  ACADEMIC_BUILDING: "Учебный корпус",
  LIBRARY: "Библиотека",
  CANTEEN: "Столовая",
  SPORTS_COMPLEX: "Спорткомплекс",
  MEDICAL_CENTER: "Медпункт",
};

export const CATEGORY_TRANSLATIONS = {
  ACCOMMODATION: "Расселение",
  BATHROOM: "Санузел",
  ELECTRICITY: "Электричество",
  HEATING: "Отопление",
  CLEANLINESS: "Чистота",
  NOISE: "Шум",
  PLUMBING: "Сантехника",
  FURNITURE: "Мебель",
  INTERNET: "Интернет",
  OTHER: "Другое",
};

export const TIMEFRAME_TRANSLATIONS = {
  ONE_DAY: "1 день",
  TWO_DAYS: "2 дня",
  THREE_DAYS: "3 дня",
  FIVE_DAYS: "5 дней",
  ONE_WEEK: "1 неделя",
  TWO_WEEKS: "2 недели",
  ONE_MONTH: "1 месяц",
};

/**
 * @param {string|null|undefined} value   – значение enum (например "COMPLAINT")
 * @param {Record<string,string>} dict    – словарь переводов
 * @param {string}                  [fallback=""] – что вернуть, если перевод не найден
 * @returns {string} русский перевод или fallback
 */
export function translate(value, dict, fallback = "") {
  if (value == null) return fallback;
  const key = typeof value === "string" ? value.trim() : String(value);
  return dict[key] ?? fallback;
}
