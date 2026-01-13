# AI Sales Agent - Testing & Setup Guide

This guide walks you through setting up and testing the AI Sales Agent system prompt in Claude.

---

## Table of Contents
1. [Quick Start (5 Minutes)](#quick-start-5-minutes)
2. [Step-by-Step Setup](#step-by-step-setup)
3. [Testing Methods](#testing-methods)
4. [Test Scenarios](#test-scenarios)
5. [Troubleshooting](#troubleshooting)

---

## Quick Start (5 Minutes)

### Fastest Way to Test

1. **Open Claude.ai** → Go to [claude.ai](https://claude.ai)
2. **Create a Project** → Click "Projects" → "Create Project"
3. **Name it** → "AI Sales Agent Test"
4. **Add Instructions** → Paste the system prompt into "Project Instructions"
5. **Customize** → Replace the Company & Product Context placeholders
6. **Start chatting** → Test with "Hi, I'm interested in your product"

---

## Step-by-Step Setup

### Method 1: Claude Projects (Recommended for Testing)

**Step 1: Create a New Project**
```
Claude.ai → Projects (left sidebar) → Create Project
```

**Step 2: Configure Project**
- **Name:** AI Sales Agent - [Your Company]
- **Description:** Sales agent for [product/service]

**Step 3: Add System Prompt**
- Click "Project Instructions" (or the settings gear)
- Paste the entire `ai_sales_agent_system_prompt.md` content
- This becomes the system prompt for all conversations in this project

**Step 4: Customize Company Context**
- Find the `## Company & Product Context` section
- Replace all placeholders with your information (see example below)

**Step 5: Save and Test**
- Start a new conversation within the project
- The AI will now behave as your sales agent

---

### Method 2: Direct Chat (Quick Testing)

**Step 1: Start New Conversation**
- Go to Claude.ai
- Click "New Chat"

**Step 2: Paste System Prompt First**
- In your first message, paste:
```
Please follow these instructions for our conversation:

[PASTE ENTIRE SYSTEM PROMPT HERE]

---

Now, let's begin. I'll play the role of a prospect. Start by greeting me.
```

**Step 3: Test the Conversation**
- Continue chatting as a prospect would
- The AI will follow the sales agent instructions

---

### Method 3: Claude API (For Developers)

```python
import anthropic

client = anthropic.Anthropic(api_key="your-api-key")

# Load your system prompt
with open("ai_sales_agent_system_prompt.md", "r") as f:
    system_prompt = f.read()

# Make API call
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system=system_prompt,
    messages=[
        {"role": "user", "content": "Hi, I'm interested in your product"}
    ]
)

print(response.content[0].text)
```

---

## How to Fill In Company Context

### Template with Example

Here's the Company & Product Context section with a real example:

```markdown
## Company & Product Context

### Company Information
- **Company Name:** FitLife Coaching
- **Industry:** Online Fitness Coaching
- **Website:** https://fitlifecoaching.com
- **Mission:** Help busy professionals get fit without sacrificing their lifestyle.

### Brand Voice
- **Tone:** Friendly, motivating, empathetic but direct
- **Words We Use:** "Partner", "Journey", "Sustainable", "Lifestyle"
- **Words We Avoid:** "Diet", "Restriction", "Punishment", "Contract"

### Products/Services

#### FitLife Transformation Program
- **Description:** 12-week personalized fitness and nutrition coaching program with weekly check-ins, custom workout plans, and flexible meal guidance.
- **Target Customer:** Busy professionals (30-50) who've tried and failed with generic programs.
- **Key Benefits:**
  - Personalized workout plans (not cookie-cutter)
  - Flexible nutrition (no restrictive diets)
  - Weekly 1-on-1 coaching calls
  - 24/7 chat support with your coach
  - Sustainable results that last
- **Price:** $297/month (3-month minimum commitment)
- **Differentiators:** Real human coaches (not just an app), flexible approach, focus on habits not just workouts

#### FitLife Starter
- **Description:** Self-paced program with video workouts and meal guides.
- **Target Customer:** Those wanting to try before committing to full coaching.
- **Key Benefits:** Access to workout library, basic meal templates, community support
- **Price:** $49/month (no commitment)
- **Differentiators:** Low-risk entry point, upgrade path to full coaching

### Pricing & Packages

| Package | Price | Includes | Best For |
|---------|-------|----------|----------|
| Starter | $49/mo | Video library, meal guides, community | Testing the waters |
| Transformation | $297/mo | Full coaching, custom plans, weekly calls | Serious commitment |
| VIP | $597/mo | Everything + daily check-ins, priority support | Accelerated results |

### Guarantees & Policies
- **Refund Policy:** 30-day money-back guarantee on Transformation program
- **Trial Period:** 7-day free trial on Starter plan
- **Cancellation:** Cancel anytime after initial 3-month commitment
- **Support:** 24/7 chat with coach; weekly video calls

### Social Proof
- **Customer Count:** 2,500+ transformations completed
- **Key Results:** "Average client loses 15-20 lbs and gains significant energy in 12 weeks"
- **Notable Clients:** Featured in Men's Health, Women's Fitness
- **Testimonials:** "I finally found something that works with my crazy schedule" - Sarah M.

### Competitors & Differentiation

| Competitor | How We Differ |
|------------|---------------|
| Noom | We have real human coaches, not just an app |
| Personal trainers | We're more affordable and flexible with scheduling |
| Beach Body | Our nutrition is flexible, not restrictive meal plans |
| MyFitnessPal | We provide accountability and coaching, not just tracking |

### Common FAQs

**Q: I've tried everything and nothing works. Why would this be different?**
A: Most programs fail because they're generic and restrictive. We build everything around YOUR life, YOUR schedule, and YOUR preferences. Plus, you have a real coach keeping you accountable.

**Q: I don't have time to work out for hours.**
A: Our workouts are 30-45 minutes, 4x per week. We design them for busy people—that's our specialty.

**Q: What if I travel a lot for work?**
A: We create travel-friendly workouts and nutrition strategies. Many of our most successful clients are frequent travelers.

**Q: Can I eat out / drink alcohol?**
A: Absolutely. We teach you how to navigate real life, including restaurants, social events, and yes, the occasional drink.

**Q: What happens after 12 weeks?**
A: You'll have the habits and knowledge to continue on your own. Many clients choose to continue with monthly maintenance coaching.

### Agent Boundaries

**CAN Promise:**
- 30-day money-back guarantee
- Weekly coaching calls
- Personalized plans (not templates)
- 24/7 chat support
- Free initial consultation call

**CANNOT Promise:**
- Specific weight loss numbers (can share typical results)
- Medical advice
- Custom pricing or discounts without manager approval
- Guaranteed results

### Escalation Contacts
- **Sales Questions:** Offer to schedule a free consultation call
- **Technical Issues:** Direct to support@fitlifecoaching.com
- **Billing Questions:** Direct to billing@fitlifecoaching.com
- **Complaints:** Offer to connect with a senior coach
```

---

## Testing Methods

### Manual Testing Checklist

Test each of these scenarios to ensure the agent works correctly:

#### Basic Functionality
- [ ] Agent introduces itself with AI disclosure
- [ ] Agent asks for prospect's name
- [ ] Agent uses prospect's name throughout
- [ ] Agent follows CLOSER framework naturally
- [ ] Agent ends conversations properly

#### Company Context
- [ ] Agent knows company name and describes it correctly
- [ ] Agent knows product details and pricing
- [ ] Agent can answer FAQs accurately
- [ ] Agent mentions correct guarantees/policies
- [ ] Agent uses brand voice appropriately

#### Objection Handling
- [ ] Handles "too expensive" objection
- [ ] Handles "need to think about it" objection
- [ ] Handles "need to ask spouse" objection
- [ ] Handles "I've tried everything" objection
- [ ] Handles "no time" objection

#### Safety & Compliance
- [ ] Discloses AI nature when asked
- [ ] Offers human handoff when appropriate
- [ ] Doesn't make unauthorized promises
- [ ] Includes disclaimers when needed
- [ ] Handles frustrated prospects appropriately

---

## Test Scenarios

Copy and paste these as prospect messages to test the agent:

### Scenario 1: Basic Inquiry
```
Hi, I saw your ad and wanted to learn more about what you offer.
```

### Scenario 2: Price Objection
```
That sounds interesting but $297/month is way more than I was expecting to spend.
```

### Scenario 3: Skeptical Prospect
```
I've tried so many programs before and nothing works. Why would this be any different?
```

### Scenario 4: Time Objection
```
I really want to do this but I work 60 hours a week. I just don't have time.
```

### Scenario 5: Spouse Objection
```
This sounds great but I need to run it by my wife first before I commit to anything.
```

### Scenario 6: AI Skepticism
```
Wait, am I talking to a real person or is this a bot?
```

### Scenario 7: Request for Human
```
Can I just speak to someone on your team directly?
```

### Scenario 8: Frustrated Prospect
```
I've been trying to get help for 20 minutes and no one is answering my actual question!
```

### Scenario 9: Ready to Buy
```
Okay, I'm sold. How do I sign up for the Transformation program?
```

### Scenario 10: Says No
```
Thanks for the information but I'm going to pass for now. It's just not the right time.
```

### Scenario 11: Competitor Comparison
```
How is this different from Noom? I've been looking at them too.
```

### Scenario 12: Detailed Question
```
What exactly happens on the weekly coaching calls? How long are they and what do you cover?
```

---

## Sample Test Conversation

Here's what a good test conversation should look like:

---

**You (as prospect):** Hi, I'm interested in getting in shape

**Agent (expected response):**
> Hi there! 👋 I'm Blake, an AI sales assistant with FitLife Coaching. I'm here to help you find the right fitness solution.
>
> Before we dive in, I'd love to know—what's your name?

**You:** I'm Mike

**Agent (expected response):**
> Great to meet you, Mike! I'm really glad you're here.
>
> So tell me, Mike, what's going on that made you want to focus on getting in shape right now?

**You:** I've gained about 30 pounds over the last few years and I just feel terrible. No energy, clothes don't fit...

**Agent (expected response):**
> I really appreciate you sharing that, Mike. That's frustrating—when your body doesn't feel like your own and it's affecting your daily life.
>
> When you think about where you want to be, what does that look like for you? What's the goal you're really after?

*[Conversation continues through CLOSER framework...]*

---

## Troubleshooting

### Agent doesn't follow instructions
- **Check:** Is the full system prompt in Project Instructions?
- **Fix:** Make sure you pasted the complete prompt, not just part of it

### Agent gives wrong product/pricing info
- **Check:** Did you customize the Company Context section?
- **Fix:** Replace all placeholder text with your actual information

### Agent doesn't disclose AI nature
- **Check:** Is the AI Disclosure section intact in the prompt?
- **Fix:** Ensure you didn't accidentally delete that section

### Agent is too pushy/salesy
- **Check:** Review the tone in your Brand Voice section
- **Fix:** Add clearer guidance about consultative approach

### Agent doesn't know how to answer a question
- **Check:** Is that information in the FAQs or Product sections?
- **Fix:** Add the missing information to Company Context

### Agent makes unauthorized promises
- **Check:** Is the "Agent Boundaries" section filled in?
- **Fix:** Be explicit about what CAN and CANNOT be promised

---

## Quick Reference: Where to Test

| Method | Best For | Setup Time |
|--------|----------|------------|
| **Claude Projects** | Ongoing testing, team access | 5 minutes |
| **Direct Chat** | Quick one-off tests | 1 minute |
| **API** | Integration testing, automation | 15+ minutes |

---

## Next Steps After Testing

1. **Refine the prompt** based on test results
2. **Add more FAQs** for questions the agent struggled with
3. **Adjust tone** if it doesn't match your brand
4. **Expand product details** if answers were too vague
5. **Test with real scenarios** from your actual sales conversations
6. **Get team feedback** by sharing the Project with colleagues

---

*Once testing is complete, you can deploy the agent via API integration, embed it in your website chat, or connect it to your CRM/sales tools.*
