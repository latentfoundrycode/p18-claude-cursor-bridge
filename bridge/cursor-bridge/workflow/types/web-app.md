# Web app

## Set at intake.delivery-kind

web-deployment

## Add at project-end.delivery for web-deployment

- **Deploy the release** (a hosted web application): the owner says yes first, since a deployment acts outside the repository and a revert does not undo it. The release's commit on `main` is then deployed to the server the owner operates by the deployment procedure, recorded in `docs/INVENTORY.md` (Resources: the host, its platform and account, the command that deploys) before the first deployment; the supervisor runs it, or the owner through a run sheet where it needs a key the session does not hold. Where the release changes how stored data is kept, the owner's live data is backed up before the deployment and migrated as part of it, never apart from a release (founding rule N1). The deployed product is then checked at its address with requests that change no user's data: it answers, and it reports the release's version. A check that fails is a defect like any other, and the previous release is deployed again by the same procedure, the backup restored where a migration ran. The report and the User Manual name the address and the version deployed.
