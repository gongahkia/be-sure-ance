import { readFileSync } from "node:fs";
import { deflateSync, inflateSync } from "node:zlib";

const MAX_PLANS_PER_BRIEF = 10;
const MASCOT = loadMascot();
const QUALITATIVE_FIELDS = [
  ["coverage_tags", "Coverage"],
  ["panel_hospitals", "Panel hospitals"],
  ["waiting_periods", "Waiting periods"],
  ["claim_deadlines", "Claim deadlines"],
  ["claim_sla", "Claim SLA"],
  ["exclusions", "Exclusions"],
  ["source_notes", "Source notes"],
];
const NO_ADVICE_DISCLAIMER =
  "This brief is for pre-meeting research only. It is not financial advice, insurance advice, legal advice, a recommendation, a ranking, a quote, or a policy transaction. Verify every fact against the carrier source, compareFIRST where applicable, and the adviser licensed compliance workflow.";

export default async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204 });
  }
  if (req.method !== "POST") {
    return jsonError("Method not allowed.", 405);
  }

  let payload;
  try {
    payload = await req.json();
  } catch {
    return jsonError("Invalid JSON payload.", 400);
  }

  const plans = Array.isArray(payload?.plans) ? payload.plans : [];
  if (plans.length === 0 || plans.length > MAX_PLANS_PER_BRIEF) {
    return jsonError(`PDF briefs support 1-${MAX_PLANS_PER_BRIEF} plans.`, 400);
  }

  const pdf = buildPdf(
    briefLines(plans, payload?.branding || {}, payload?.options || {}),
  );
  return new Response(pdf, {
    headers: {
      "Content-Type": "application/pdf",
      "Content-Disposition":
        'attachment; filename="be-sure-ance-client-brief.pdf"',
      "Cache-Control": "no-store",
    },
  });
};

export const config = {
  method: ["OPTIONS", "POST"],
  path: "/briefs/client.pdf",
};

function jsonError(message, status) {
  return Response.json({ detail: message }, { status });
}

function briefLines(plans, branding, options = {}) {
  const lines = [
    "Be-sure-ance Client Brief",
    `Generated at ${new Date().toISOString().replace(/\.\d{3}Z$/, "+00:00")}`,
    "",
    NO_ADVICE_DISCLAIMER,
    "",
    brandingFooterText(branding),
    "",
  ];

  for (const plan of plans) {
    lines.push(planHeading(plan));
    for (const [fieldName, label] of QUALITATIVE_FIELDS) {
      lines.push(`${label}: ${fieldText(plan, fieldName)}`);
    }
    const sources = sourceLines(plan);
    lines.push("Sources:");
    lines.push(...(sources.length ? sources : ["No sources"]));
    if (options.include_plan_details !== false) {
      lines.push(
        `Overview: ${safeText(plan.plan_overview || plan.plan_description) || "Unknown"}`,
      );
      lines.push(
        `Benefits: ${(plan.plan_benefits || []).map(safeText).filter(Boolean).join("; ") || "Unknown"}`,
      );
      lines.push(`Product page: ${safeText(plan.plan_url) || "Not provided"}`);
      lines.push(
        `Brochure: ${safeText(plan.product_brochure_url) || "Not provided"}`,
      );
    }
    lines.push("");
  }
  return lines.flatMap((line) => wrapLine(line, 92)).slice(0, 62);
}

function planHeading(plan) {
  const provider = safeText(
    plan.canonical_carrier_name || plan.providerName || plan.insurer,
  );
  const planName = safeText(plan.plan_name);
  return provider ? `${provider}: ${planName}` : planName;
}

function fieldText(plan, fieldName) {
  const fieldValue = plan?.facts?.[fieldName]?.field_value || {};
  if (fieldValue.status && fieldValue.status !== "known") {
    return safeText(fieldValue.status);
  }
  if (fieldName === "claim_sla") {
    const value = fieldValue.value || {};
    if (value.duration_days) {
      return `${value.duration_days} days${value.basis ? ` (${safeText(value.basis)})` : ""}`;
    }
  }
  const items = Array.isArray(fieldValue.items) ? fieldValue.items : [];
  return (
    items
      .map((item) => itemText(item, fieldName))
      .filter(Boolean)
      .join("; ") || "Unknown"
  );
}

function itemText(item, fieldName) {
  if (typeof item === "string") {
    return safeText(item);
  }
  if (!item || typeof item !== "object") {
    return "";
  }
  if (fieldName === "waiting_periods" && item.duration_days !== undefined) {
    return `${safeText(item.condition)}: ${item.duration_days} days`;
  }
  if (fieldName === "claim_deadlines" && item.deadline_days !== undefined) {
    return `${safeText(item.event)}: ${item.deadline_days} days`;
  }
  return safeText(
    item.normalized_name ||
      item.name ||
      item.label ||
      item.condition ||
      item.event ||
      item.details ||
      item.raw_text,
  );
}

function sourceLines(plan) {
  return QUALITATIVE_FIELDS.map(([fieldName, label]) => {
    const fact = plan?.facts?.[fieldName] || {};
    if (!fact.source_url) {
      return "";
    }
    const sourceType = fact.source_type || "source";
    const verifiedAt = fact.last_verified_at || "verification missing";
    return `${label}: ${sourceType}; verified ${verifiedAt}; ${fact.source_url}`;
  }).filter(Boolean);
}

function brandingFooterText(branding) {
  const agentName = safeText(branding.agent_name || branding.agentName);
  const masRepNumber = safeText(
    branding.mas_rep_number || branding.masRepNumber,
  );
  if (agentName && masRepNumber) {
    return `Prepared by ${agentName} | MAS rep no. ${masRepNumber}`;
  }
  if (agentName) {
    return `Prepared by ${agentName} | MAS rep no. not provided`;
  }
  if (masRepNumber) {
    return `Prepared by unbranded adviser | MAS rep no. ${masRepNumber}`;
  }
  return "Prepared by unbranded adviser | MAS rep no. not provided";
}

function buildPdf(lines) {
  const textOps = lines
    .map((line, index) => {
      const x = index < 2 && MASCOT ? 90 : 50;
      const y = 790 - index * 12;
      const isLink = /https?:\/\//.test(line);
      const color = isLink ? "0.114 0.306 0.85" : "0 0 0";
      const underline = isLink
        ? `q\n${color} RG\n0.5 w\n${x} ${y - 1} m\n545 ${y - 1} l\nS\nQ\n`
        : "";
      return `BT\n/F1 9 Tf\n${color} rg\n1 0 0 1 ${x} ${y} Tm\n(${pdfText(line)}) Tj\nET\n${underline}`;
    })
    .join("\n");
  const mascotOps = MASCOT ? `q\n32 0 0 32 50 771 cm\n/Im1 Do\nQ\n` : "";
  const content = `${mascotOps}${textOps}`;
  const resources = MASCOT
    ? "<< /Font << /F1 4 0 R >> /XObject << /Im1 6 0 R >> >>"
    : "<< /Font << /F1 4 0 R >> >>";
  const objects = [
    "<< /Type /Catalog /Pages 2 0 R >>",
    "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources ${resources} /Contents 5 0 R >>`,
    "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    `<< /Length ${Buffer.byteLength(content)} >>\nstream\n${content}\nendstream`,
  ];
  if (MASCOT) {
    objects.push(
      Buffer.concat([
        Buffer.from(
          `<< /Type /XObject /Subtype /Image /Width ${MASCOT.width} /Height ${MASCOT.height} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode /Length ${MASCOT.data.length} >>\nstream\n`,
        ),
        MASCOT.data,
        Buffer.from("\nendstream"),
      ]),
    );
  }

  const chunks = [Buffer.from("%PDF-1.4\n")];
  const offsets = [0];
  let length = chunks[0].length;
  for (const [index, object] of objects.entries()) {
    const body = Buffer.isBuffer(object) ? object : Buffer.from(object);
    const wrapped = Buffer.concat([
      Buffer.from(`${index + 1} 0 obj\n`),
      body,
      Buffer.from("\nendobj\n"),
    ]);
    offsets.push(length);
    chunks.push(wrapped);
    length += wrapped.length;
  }
  const xrefOffset = length;
  const trailer = [
    `xref\n0 ${objects.length + 1}\n`,
    "0000000000 65535 f \n",
    ...offsets
      .slice(1)
      .map((offset) => `${String(offset).padStart(10, "0")} 00000 n \n`),
    `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF\n`,
  ].join("");
  chunks.push(Buffer.from(trailer));
  return Buffer.concat(chunks);
}

function loadMascot() {
  try {
    return pngToPdfImage(
      readFileSync(new URL("./mascot.png", import.meta.url)),
    );
  } catch {
    return null;
  }
}

function pngToPdfImage(buffer) {
  if (buffer.toString("ascii", 1, 4) !== "PNG") {
    throw new Error("Expected PNG mascot.");
  }
  let offset = 8;
  let width = 0;
  let height = 0;
  let bitDepth = 0;
  let colorType = 0;
  const idat = [];
  while (offset < buffer.length) {
    const length = buffer.readUInt32BE(offset);
    const type = buffer.toString("ascii", offset + 4, offset + 8);
    const data = buffer.subarray(offset + 8, offset + 8 + length);
    offset += length + 12;
    if (type === "IHDR") {
      width = data.readUInt32BE(0);
      height = data.readUInt32BE(4);
      bitDepth = data[8];
      colorType = data[9];
    }
    if (type === "IDAT") idat.push(data);
    if (type === "IEND") break;
  }
  if (bitDepth !== 8 || ![2, 6].includes(colorType)) {
    throw new Error("Mascot PNG must use 8-bit RGB or RGBA colour.");
  }

  const channels = colorType === 6 ? 4 : 3;
  const scanlines = inflateSync(Buffer.concat(idat));
  const stride = width * channels;
  const rgb = Buffer.alloc(width * height * 3);
  let previous = Buffer.alloc(stride);
  let sourceOffset = 0;
  let targetOffset = 0;
  for (let rowIndex = 0; rowIndex < height; rowIndex += 1) {
    const filter = scanlines[sourceOffset];
    sourceOffset += 1;
    const row = Buffer.from(
      scanlines.subarray(sourceOffset, sourceOffset + stride),
    );
    sourceOffset += stride;
    unfilterPngRow(row, previous, filter, channels);
    for (let pixel = 0; pixel < width; pixel += 1) {
      const source = pixel * channels;
      const alpha = channels === 4 ? row[source + 3] / 255 : 1;
      rgb[targetOffset++] = Math.round(row[source] * alpha + 255 * (1 - alpha));
      rgb[targetOffset++] = Math.round(
        row[source + 1] * alpha + 255 * (1 - alpha),
      );
      rgb[targetOffset++] = Math.round(
        row[source + 2] * alpha + 255 * (1 - alpha),
      );
    }
    previous = row;
  }
  return { width, height, data: deflateSync(rgb) };
}

function unfilterPngRow(row, previous, filter, bytesPerPixel) {
  for (let index = 0; index < row.length; index += 1) {
    const left = index >= bytesPerPixel ? row[index - bytesPerPixel] : 0;
    const up = previous[index] || 0;
    const upLeft =
      index >= bytesPerPixel ? previous[index - bytesPerPixel] || 0 : 0;
    if (filter === 1) row[index] = (row[index] + left) & 255;
    if (filter === 2) row[index] = (row[index] + up) & 255;
    if (filter === 3)
      row[index] = (row[index] + Math.floor((left + up) / 2)) & 255;
    if (filter === 4) row[index] = (row[index] + paeth(left, up, upLeft)) & 255;
  }
}

function paeth(left, up, upLeft) {
  const estimate = left + up - upLeft;
  const leftDistance = Math.abs(estimate - left);
  const upDistance = Math.abs(estimate - up);
  const upLeftDistance = Math.abs(estimate - upLeft);
  if (leftDistance <= upDistance && leftDistance <= upLeftDistance) return left;
  return upDistance <= upLeftDistance ? up : upLeft;
}

function wrapLine(value, limit) {
  const words = safeText(value).split(" ");
  const lines = [];
  let current = "";
  for (const word of words) {
    if (`${current} ${word}`.trim().length > limit) {
      lines.push(current);
      current = word;
    } else {
      current = `${current} ${word}`.trim();
    }
  }
  if (current || lines.length === 0) {
    lines.push(current);
  }
  return lines;
}

function pdfText(value) {
  return safeText(value).replace(/[\\()]/g, "\\$&");
}

function safeText(value) {
  return String(value || "")
    .replace(/\s+/g, " ")
    .trim();
}
