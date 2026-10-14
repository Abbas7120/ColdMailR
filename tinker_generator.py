import sys, json, os, re
from dotenv import load_dotenv

load_dotenv()

MODEL = "Qwen/Qwen3-8B"
NUM_CANDIDATES = 3

SYSTEM_PROMPT = """You are an expert career coach who writes cold emails from a job seeker to a hiring manager or team member.

You receive: Company, Role, Achievement (the candidate's own words).

HARD RULES
1. The sender is the CANDIDATE applying for the role. Never write as a customer, vendor or salesperson.
2. Use ONLY facts given in the input. Never invent numbers, tools, projects, awards, company news, products, funding or people.
3. Copy every number from the Achievement exactly as typed (write 500000 as 500000, not 5 lakh or 500K). Use no other numbers except "10" for the 10-minute chat.
4. Never claim to know specifics about the company. Connect the company name to the core work of the role instead.
5. If the Achievement is short or vague, keep the email short. Do not pad it or fabricate detail.
6. The role can be in any field (tech, sales, marketing, design, finance, operations, teaching, healthcare, internships, freshers). Adapt vocabulary to that field.
7. Rewrite the Achievement in fluent first person, in your own words. Do not copy its sentences. Keep the facts and numbers, shorten it to its strongest point, then add one short clause on why it matters for this role.

FORMAT (follow exactly)
Subject: <max 8 words, include the role or the achievement, no emojis>

Hi there,

<Sentence 1: why this role at this company, in terms of the role's work.>

<Sentence 2-3: the achievement, then how it helps in this role.>

<Sentence 4: one low-pressure ask for a 10-minute chat about the role.>

Best,
[Your Name]

STYLE
- Body 50 to 100 words. Plain, confident, human. No clichés such as "I hope this finds you well", "passionate", "rockstar", "synergy", "excited to leverage".
- Output ONLY the email. No notes, no markdown, no quotation marks, no placeholders other than [Your Name]."""

EXAMPLES = [
    ("Company: Notion\nRole: Frontend Engineer\nAchievement: Rebuilt a dashboard in React, cutting load time by 35%",
"""Subject: Frontend Engineer - cut dashboard load time 35%

Hi there,

A fast, clean interface is at the heart of Notion's product, which is why the Frontend Engineer role stands out to me.

I recently rebuilt a dashboard in React and cut its load time by 35%. I'd like to bring that focus on performance to your team.

Would you be open to a 10-minute chat about the role?

Best,
[Your Name]"""),
    ("Company: HubSpot\nRole: Content Marketing Manager\nAchievement: Grew a SaaS blog from 8k to 40k monthly visitors in one year through SEO and email",
"""Subject: Content Marketing Manager - grew blog 8k to 40k

Hi there,

Content that educates first and sells second is central to HubSpot's marketing, and that is the work I want to do as your Content Marketing Manager.

I grew a SaaS blog from 8k to 40k monthly visitors in one year through SEO and email, and I'd like to apply that same approach to HubSpot's content.

Could we have a 10-minute chat about where the team is headed?

Best,
[Your Name]"""),
    ("Company: Deloitte\nRole: Analyst Intern\nAchievement: Final-year commerce student, led a college finance club and built a stock analysis project in Excel",
"""Subject: Analyst Intern - finance club lead, Excel project

Hi there,

Analysts at Deloitte turn raw numbers into clear advice, and that is the skill I am working to build as an Analyst Intern.

As a final-year commerce student, I led our college finance club and built a stock analysis project in Excel. I would like to grow those skills on a real team.

Would you be open to a 10-minute chat about the internship?

Best,
[Your Name]"""),
    ("Company: Unacademy\nRole: Sales Representative\nAchievement: Campus ambassador who sold 200 courses and earned 150000 in revenue for the company",
"""Subject: Sales Representative - sold 200 courses, 150000 revenue

Hi there,

Helping students find the right course is the heart of a Sales Representative role at Unacademy, and it is work I have already done.

As a campus ambassador, I sold 200 courses and earned 150000 in revenue for the company. I would like to bring that student-facing sales experience to your team.

Would you be open to a 10-minute chat about the role?

Best,
[Your Name]"""),
]

BANNED = ["i hope this", "passionate", "rockstar", "synergy", "leverage", "<|", "[first name]", "[company]", "[role]", "hi team"]


def clean(text):
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = text.split("<|im_end|>")[0].split("<|im_start|>")[0]
    text = text.replace("**", "").replace("```", "").strip()
    idx = text.find("Subject:")
    if idx > 0:
        text = text[idx:]
    return text.strip().strip('"').strip()


def numbers_in(s):
    return set(re.findall(r"\d+(?:\.\d+)?", s.replace(",", "")))


def issues(email, company, role, highlight):
    """Return (hard_problems, soft_problems)."""
    hard, soft = [], []
    if not email.startswith("Subject:"):
        hard.append("missing subject")
    if "\n" not in email:
        hard.append("no body")
        return hard, soft
    body = email.split("\n", 1)[1]
    if "Hi there," not in body:
        soft.append("greeting")
    if "[Your Name]" not in body:
        soft.append("sign-off")
    words = len(body.split())
    if words < 35 or words > 140:
        soft.append("length")
    low = email.lower()
    if any(b in low for b in BANNED):
        soft.append("banned phrase")
    if company.lower() not in low:
        soft.append("company missing")
    allowed = numbers_in(highlight) | numbers_in(role) | numbers_in(company) | {"10"}
    if not numbers_in(email).issubset(allowed):
        soft.append("invented number")
    if ("> " + highlight[:20].lower()) in low:
        soft.append("pasted quote")
    return hard, soft


def build_prompt(company, role, highlight):
    p = f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
    for user, reply in EXAMPLES:
        p += f"<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n{reply}<|im_end|>\n"
    p += (f"<|im_start|>user\nCompany: {company}\nRole: {role}\nAchievement: {highlight}<|im_end|>\n"
          "<|im_start|>assistant\n<think>\n\n</think>\n\n")
    return p


def generate_cold_email(company, role, highlight):
    import tinker
    from tinker import types
    from transformers import AutoTokenizer

    if not os.getenv("TINKER_API_KEY"):
        raise RuntimeError("TINKER_API_KEY is missing from .env")

    tokenizer = AutoTokenizer.from_pretrained(MODEL)
    service_client = tinker.ServiceClient()
    sampling_client = service_client.create_sampling_client(base_model=MODEL)

    ids = tokenizer(build_prompt(company, role, highlight), add_special_tokens=False)["input_ids"]
    model_input = types.ModelInput.from_ints(ids)
    params = types.SamplingParams(max_tokens=300, temperature=0.5, stop=["<|im_end|>"])

    result = sampling_client.sample(
        prompt=model_input, num_samples=NUM_CANDIDATES, sampling_params=params
    ).result()

    best, best_score = None, None
    for seq in result.sequences:
        email = clean(tokenizer.decode(seq.tokens))
        hard, soft = issues(email, company, role, highlight)
        if hard:
            print("Rejected:", hard, file=sys.stderr)
            continue
        score = len(soft)
        if best_score is None or score < best_score:
            best, best_score = email, score
        if score == 0:
            break
    if best is None:
        raise RuntimeError("The model returned no usable email. Please try again.")
    if best_score:
        print("Used best candidate with minor issues:", best_score, file=sys.stderr)
    return best


if __name__ == "__main__":
    try:
        data = json.loads(sys.stdin.read())
        email = generate_cold_email(
            data.get("company", "").strip(),
            data.get("role", "").strip(),
            data.get("highlight", "").strip(),
        )
        print(json.dumps({"email": email}, ensure_ascii=False))
    except Exception as e:
        print(f"{type(e).__name__}: {e}", file=sys.stderr)
        print(json.dumps({"error": f"{type(e).__name__}: {e}"}, ensure_ascii=False))
        sys.exit(1)