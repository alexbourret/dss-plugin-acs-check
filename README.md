# ACS Checker plugin for Dataiku DSS

This plugin helps identify SharePoint connections still using the deprecated **Site App Permissions** preset (ACS authentication).

Microsoft announced ACS deprecation for SharePoint Online on **April 2, 2026**. Use this plugin to find DSS objects that must be migrated to a different authentication preset.

## What this plugin does

The plugin provides one custom dataset connector:

- `acs-checker_list-used-acs-presets`

When read, the dataset scans the local DSS instance and lists SharePoint Online usages in:

- DSS recipes using the `sharepoint-online` plugin
- DSS datasets using the `sharepoint-online` plugin
- DSS managed folders of SharePoint type

For each detected object, it outputs a status:

- `KO`: object uses `site-app-permissions` and should be updated
- `OK`: object does not use `site-app-permissions`

If your DSS `studioExternalUrl` is correctly configured, the `To check` column contains a direct link to the settings page of flagged objects.

## Prerequisites

- A Dataiku DSS instance where this plugin is installed
- The **SharePoint Online** plugin installed (`sharepoint-online`)
- Permissions allowing the scan of projects, plugin usages, datasets, recipes, and managed folders
- `studioExternalUrl` configured in DSS general settings (to generate clickable links in `To check`)

## Installation

Choose one installation method.

### Option 1: Install from plugin archive (UI)

1. Package this repository as a zip archive.
2. In DSS, go to **Administration > Plugins > Installed**.
3. Click **+ Install Plugin**.
4. Upload the archive and install.

### Option 2: Install from Git

1. In DSS, go to **Administration > Plugins > Installed**.
2. Click **+ Install Plugin**.
3. Choose Git-based installation and use:
   - `https://github.com/alexbourret/dss-plugin-acs-check`
4. Install and restart code environments if requested.

## How to use

1. In a project, create a new dataset.
2. Select the plugin connector **Custom dataset acs-checker_list-used-acs-presets**.
3. In the dataset settings, optionally set the `Project` box:
   - set a DSS project ID to scan only that project
   - leave it empty to scan all projects in the instance
4. Build/read the dataset.
5. Filter on `Status = KO` to list objects that require migration.
6. Open links in `To check` and update the SharePoint preset.

## Output columns

Typical columns returned by the dataset:

- `dss_client`: DSS base URL used to build links
- `element_type`: detected element type
- `kind`: object category
- `project_key`: DSS project key
- `object_id`: recipe/dataset/folder identifier
- `Preset name`: ACS preset name used by flagged objects, or `Manually defined`
- `Status`: `OK` or `KO`
- `To check`: settings URL for flagged objects

## Operational notes

- The dataset is read-only.
- The plugin detects deprecated ACS usage by checking `auth_type == site-app-permissions`.
- If `Project` is set, only that project is scanned.
- If `Project` is empty, the scan covers all projects accessible to the executing user/API context.

## Suggested remediation workflow

1. Run the checker dataset.
2. Export or share rows with `Status = KO`.
3. Update each SharePoint connection/preset to a supported alternative.
4. Rebuild the checker dataset until no `KO` rows remain.

## Version

- Plugin ID: `acs-checker`
- Current version: `0.0.3`
