# Web app

## Set at intake.delivery-kind

web-deployment

## Add at project-end.delivery for web-deployment

- **Deploy the release** (a hosted web application), in this order, each step only after the one before it has succeeded:
  1. **The owner's yes**, first, since a deployment acts outside the repository and a revert does not undo it: the yes names the release, the pause in writes step 3 makes, and the way back in step 6. The deployment procedure is recorded in `docs/INVENTORY.md` (Resources: the host, its platform and account, the command that deploys) before the first deployment; the supervisor runs it, or the owner through a run sheet where it needs a key the session does not hold.
  2. **The rehearsal**, where the release changes how stored data is kept: its migration runs on a copy restored from a backup of the live data, kept away from the repository and the Workspace as the backup in step 3 is, which also proves the backup restores, and its result is checked there. A rehearsal that fails stops the deployment before anything live is touched; it is a defect like any other.
  3. **The backup and the pause.** Immediately before the deployment the owner's live data is backed up, to storage on the platform or of the owner's that Resources records with its platform and account, never into the repository or the Workspace, since it holds the users' data; from that backup until step 5 passes, the product takes no writes (a maintenance or read-only mode, or offline where it has neither), so that no user's write is lost whichever way the deployment goes.
  4. **The deployment.** The release's commit on `main` is deployed by the recorded procedure, and its migration runs on the live data only here, as part of the deployment, never apart from a release (the design's migration policy, and founding rule N1's principle).
  5. **The check.** The deployed product is checked at its address with requests that change no user's data: it answers, and it reports the release's version where the design gives the version a place, the deployed commit read from the platform otherwise. When it passes, writes resume, and the report and the User Manual name the address and the version deployed.
  6. **The way back**, when step 4 or step 5 fails, a defect like any other: where a migration ran, the backup is restored first, since the previous release may not run on migrated data; then the previous release is deployed by the same procedure and checked as in step 5, and writes resume. The pause of step 3 means the restore discards no user's write.
