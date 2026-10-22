# Stage-aware V2 demo

This demo explicitly enables lightweight capture, exercises two phases, and prepares one reviewed progress-and-screenshot record without committing, uploading, or publishing it.

```bash
python3 skill/haostory/scripts/haostory.py setup
python3 skill/haostory/scripts/haostory.py enable \
  --progress-file docs/progress.md \
  --screenshots-dir docs/screenshots

python3 skill/haostory/scripts/haostory.py suggest-start \
  --session demo-build \
  --title "Build stage-aware capture" \
  --summary "Create a deterministic V2 capture model." \
  --type software \
  --initiative capture-v2 \
  --phase build

# Run this failure command three times. It remains one event with occurrence_count=3.
python3 skill/haostory/scripts/haostory.py remember \
  --session demo-build \
  --event failure \
  --notes "The lifecycle test failed with exit code 1." \
  --novelty-key lifecycle-exit-1

python3 skill/haostory/scripts/haostory.py remember \
  --session demo-build \
  --event recovery \
  --notes "A lifecycle-state fix made the test pass." \
  --novelty-key lifecycle-exit-1 \
  --evidence-ref test:lifecycle-pass \
  --asset /tmp/stable-recovery.png \
  --data-kind demo

python3 skill/haostory/scripts/haostory.py close-phase \
  --session demo-build \
  --result "The build is runnable and ready for validation." \
  --lesson "Lifecycle behavior must be verified across phases." \
  --todo "Validate the flow with real data." \
  --handoff

# Run only after reviewing the whole phase and its selected screenshot.
python3 skill/haostory/scripts/haostory.py share-stage \
  --session demo-build \
  --confirmed

python3 skill/haostory/scripts/haostory.py start \
  --session demo-validate \
  --title "Validate stage-aware capture" \
  --summary "Test behavior and privacy boundaries." \
  --type software \
  --initiative capture-v2 \
  --phase validate

python3 skill/haostory/scripts/haostory.py remember \
  --session demo-validate \
  --event metric \
  --notes "All acceptance scenarios passed." \
  --novelty-key acceptance-pass \
  --claim "Stage-aware capture preserves V1 compatibility." \
  --evidence-ref test:acceptance-pass

python3 skill/haostory/scripts/haostory.py registry check --session demo-validate
python3 skill/haostory/scripts/haostory.py story-plan --session demo-validate
python3 skill/haostory/scripts/haostory.py audit --session demo-validate
```

Expected result:

- build and validate are independent capture windows under the same initiative;
- each phase normally retains no more than four distinct events;
- validate contains `necessary_context.source_session: demo-build`;
- three equal failures fold into one event, while recovery remains separate;
- the stable recovery screenshot is copied directly into `demo-build/assets/recovery/` without a candidates queue;
- closing on handoff writes a private stage brief and reports the assets location, but does not create exports, commit, upload, publish, or update the registry;
- `share-stage` updates `docs/progress.md`, copies the reviewed screenshot into `docs/screenshots/YYYY-MM-DD/`, and reports those files for a later user-controlled Git operation;
- the validate story plan identifies the new claim and evidence;
- no visual asset is copied and the text privacy audit passes.

`git commit`, `git push`, upload, and `registry publish` are intentionally absent. Each requires a separate user decision.
