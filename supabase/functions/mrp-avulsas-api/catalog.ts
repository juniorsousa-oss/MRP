/** Regras puras de seleção de materiais para solicitações avulsas. */
export type MrpMaterial = {codigo:string;descricao:string;saldo:number;div:number;limite:number};
export function numeric(value: unknown): number {
  if (typeof value === "number") return Number.isFinite(value) ? value : NaN;
  const raw = String(value ?? "").trim().replace(/\s/g,"");
  if (!raw) return NaN;
  const cleaned = raw.includes(",") ? raw.replace(/\./g,"").replace(",",".") : raw;
  const parsed = Number(cleaned);
  return Number.isFinite(parsed) ? parsed : NaN;
}
export function round3(value: number): number {
  return Math.round((value + Number.EPSILON) * 1000) / 1000;
}
/** Somente saldo físico positivo E sobra/DIV positiva. */
export function selectMaterial(row: Record<string, unknown>): MrpMaterial | null {
  const rawCode = String(row["Código"] ?? "").trim().replace(/\.0$/, "");
  if (!/^\d+$/.test(rawCode)) return null;
  const saldo = numeric(row["Saldo em Estoque"]);
  const div = numeric(row["DIV"]);
  if (!Number.isFinite(saldo) || !Number.isFinite(div) || saldo <= 0 || div <= 0) return null;
  const limite = round3(Math.min(saldo, div));
  if (limite <= 0) return null;
  return {
    codigo:rawCode.padStart(8,"0"),
    descricao:String(row["Descrição"] ?? "").slice(0,500),
    saldo:round3(saldo),div:round3(div),limite,
  };
}
export function availableAfterReservations(limite: number, reservado: number): number {
  return Math.max(0,round3(limite-reservado));
}
export function displayStatus(status: unknown): string {
  return ["ATENDIDA","SEPARADA"].includes(String(status)) ? "SEPARADA" : "PENDENTE";
}
