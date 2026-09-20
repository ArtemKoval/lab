export function pickCell(free, rng)
{
    if (free.length === 0) return null;
    const r = rng();
    const i = Math.floor(r * free.length);
    return free[i];
}
