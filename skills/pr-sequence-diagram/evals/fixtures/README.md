# Eval fixtures

Synthetic PR fixtures used when iterating on the skill. Each fixture is a tiny git repo with a `main` branch and a feature branch whose diff represents a common PR shape.

Fixtures are **regenerated** from `build_fixtures.sh` — they aren't checked into this repo. To (re)build them:

```bash
bash build_fixtures.sh
```

## Fixtures produced

| Fixture | Shape |
| --- | --- |
| `node-api-stripe-cancel` | new Express endpoint that cancels a Stripe subscription + updates DB + sends email |
| `python-queue-welcome-emails` | moves welcome-email sending off the signup request onto a Redis queue + worker |
| `react-onboarding-flag` | adds a feature-flag-gated onboarding flow after login |
