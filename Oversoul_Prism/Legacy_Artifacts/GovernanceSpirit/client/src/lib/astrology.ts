// client/src/lib/astrology.ts

export function getCurrentMoonPhase(): string {
  const now = new Date();
  const synodicMonth = 29.53058867;
  const newMoon = new Date('2001-01-24T13:36:00Z'); // known new moon UTC
  const daysSinceNewMoon = (now.getTime() - newMoon.getTime()) / (1000 * 60 * 60 * 24);
  const phase = daysSinceNewMoon % synodicMonth;

  if (phase < 1.84566) return 'New Moon';
  else if (phase < 5.53699) return 'Waxing Crescent';
  else if (phase < 9.22831) return 'First Quarter';
  else if (phase < 12.91963) return 'Waxing Gibbous';
  else if (phase < 16.61096) return 'Full Moon';
  else if (phase < 20.30228) return 'Waning Gibbous';
  else if (phase < 23.99361) return 'Last Quarter';
  else if (phase < 27.68493) return 'Waning Crescent';
  else return 'New Moon';
}

export function getZodiacSign(date: Date = new Date()): string {
  const day = date.getDate();
  const month = date.getMonth() + 1;

  if ((month === 3 && day >= 21) || (month === 4 && day <= 19)) return 'Aries';
  if ((month === 4 && day >= 20) || (month === 5 && day <= 20)) return 'Taurus';
  if ((month === 5 && day >= 21) || (month === 6 && day <= 20)) return 'Gemini';
  if ((month === 6 && day >= 21) || (month === 7 && day <= 22)) return 'Cancer';
  if ((month === 7 && day >= 23) || (month === 8 && day <= 22)) return 'Leo';
  if ((month === 8 && day >= 23) || (month === 9 && day <= 22)) return 'Virgo';
  if ((month === 9 && day >= 23) || (month === 10 && day <= 22)) return 'Libra';
  if ((month === 10 && day >= 23) || (month === 11 && day <= 21)) return 'Scorpio';
  if ((month === 11 && day >= 22) || (month === 12 && day <= 21)) return 'Sagittarius';
  if ((month === 12 && day >= 22) || (month === 1 && day <= 19)) return 'Capricorn';
  if ((month === 1 && day >= 20) || (month === 2 && day <= 18)) return 'Aquarius';
  if ((month === 2 && day >= 19) || (month === 3 && day <= 20)) return 'Pisces';
  return 'Unknown';
}
