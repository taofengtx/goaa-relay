# GOAA Package 3 Baton 12 — Runtime Activation Archive

## Package
Package 3 — Runtime Activation

## Scope
Local Console Runtime activation only.

## Git Truth
main HEAD:
7318eadd20984ef17aec267ffd0bb756141296b1

## Delivered chain
1. Task 1 — Runtime activation readiness audit
2. Task 2B — systemd-managed 5188 activation audit
3. Task 2C — systemd drop-in activation for 5188
4. Task 2D — Runtime activation closeout
5. Task 2E — Stop redundant 5189 dev runtime

## Runtime Truth before activation
5188 was served by systemd-managed goaa-local-console.service from:
/opt/goaa/local-console

That code was old and did not contain Package 1 / Package 2 markers.

## Runtime activation
A systemd drop-in override was created:

/etc/systemd/system/goaa-local-console.service.d/override.conf

Content:

[Service]
WorkingDirectory=/home/aika/Projects/goaa-ai-main/local-console

Then daemon-reload and restart were performed under Tao approval.

## Runtime Truth after activation
5188 is active and served by:
goaa-local-console.service

WorkingDirectory:
/home/aika/Projects/goaa-ai-main/local-console

5188 /health returned OK.
5188 served HTML contains Package 2 markers:
  - evidenceIntentLabel: 2
  - Evidence Preview · Readonly Dry-run: 1
  - evidenceSafetyLine: 2
  - td.intent==='pure_chat': 1

## 5189 cleanup
The temporary dev runtime on 127.0.0.1:5189 was stopped under Tao approval.
5189 port was released.
5188 remained healthy.

## Safety boundary
- Production deploy: NO
- DO connection: NO
- Worker started: NO
- Executor enabled: NO
- Real task execution: NO
- /tasks/run called: NO
- Real RAG query executed: NO
- Embedding rebuild executed: NO
- Secret read attempted: NO
- Private key read attempted: NO

## Rollback plan
```bash
sudo systemctl revert goaa-local-console.service
sudo systemctl daemon-reload
sudo systemctl restart goaa-local-console.service
```

## Closure status
Package 3 Runtime Activation is complete after:
- 5188 Runtime Truth aligns with Git Truth
- 5189 duplicate runtime stopped
- Baton 12 archive reviewed
