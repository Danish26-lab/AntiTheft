# Remote Data Wipe (User-Approved Folders) - User Guide

## Overview

The Remote Data Wipe feature allows you to securely delete sensitive data from a tracked device remotely. **Only folders explicitly approved by you on the device can be wiped**, ensuring system-critical files are always protected.

## Safety Features

- **User-Approved Folders Only**: The system never has unrestricted filesystem access. Only folders you explicitly approve can be wiped.
- **System Protection**: Critical system folders are automatically blocked:
  - `C:\Windows`
  - `C:\Program Files`
  - `C:\ProgramData`
  - And other system directories
- **Two-Step Confirmation**: Requires two confirmations before executing wipe
- **Real-Time Progress**: See wipe progress and status updates in real-time

## Setup Instructions

### Step 1: Approve Folders on Device

1. On the device you want to protect, navigate to the `device_agent` folder
2. Run the folder selection tool:
   ```bash
   python select_approved_folders.py
   ```
3. Click "Add Folder" to select folders you want to be eligible for remote wipe
4. Review the list and remove any folders you don't want to wipe
5. Click "Save & Sync" to save and sync to the server

**Important**: Only folders you approve here can be remotely wiped. System folders are automatically blocked.

### Step 2: Run Database Migration

On the backend server, run the migration to create the necessary database tables:

```bash
cd backend
python migrate_add_wipe_tables.py
```

### Step 3: Use Remote Wipe from Dashboard

1. Open the device detail page in the web dashboard
2. In the "Data Security" section, click "Custom Wipe"
3. Select which approved folders to wipe (or select all)
4. Review the preview of folders to be wiped
5. Confirm the action (requires two confirmations)
6. Monitor progress in real-time

## How It Works

### Architecture

1. **Folder Approval (Device-Side)**: 
   - User runs `select_approved_folders.py` on the device
   - Selected folders are saved locally and synced to backend
   - Only these folders are eligible for remote wipe

2. **Wipe Trigger (Web Dashboard)**:
   - User selects folders to wipe from approved list
   - Backend creates a wipe operation record
   - Device agent polls for pending operations

3. **Wipe Execution (Device-Side)**:
   - Agent verifies requested folders match approved folders
   - Performs secure deletion only within approved directories
   - Reports progress and status back to backend

4. **Status Tracking**:
   - Real-time progress updates (percentage, files deleted)
   - Final status (completed/failed) with error messages
   - All operations logged in activity log

### Security Model

- **No Unrestricted Access**: The system cannot wipe folders you haven't approved
- **Path Validation**: All wipe requests are validated against approved folders
- **System Protection**: Blocked paths are enforced at both UI and backend levels
- **Audit Trail**: All wipe operations are logged with timestamps and details

## API Endpoints

### For Device Agent

- `POST /api/v1/approved_folders/<device_id>` - Sync approved folders
- `GET /api/v1/wipe/pending/<device_id>` - Check for pending wipe operations
- `POST /api/v1/wipe/update_status` - Report wipe progress/status

### For Web Dashboard

- `GET /api/v1/approved_folders/<device_id>` - Get approved folders list
- `POST /api/v1/wipe/trigger` - Trigger wipe operation
- `GET /api/v1/wipe/status/<device_id>` - Get wipe operation status

## Troubleshooting

### "No approved folders found"

**Solution**: Run `select_approved_folders.py` on the device and approve at least one folder.

### Wipe operation stuck in "pending"

**Possible causes**:
- Device agent is not running
- Device is offline
- Network connectivity issues

**Solution**: 
1. Check device agent is running: `python agent.py`
2. Check device connectivity
3. Check agent logs for errors

### Folder not appearing in approved list

**Possible causes**:
- Folder path was blocked (system folder)
- Sync to server failed

**Solution**:
1. Check if folder is a system folder (will be blocked automatically)
2. Re-run `select_approved_folders.py` and sync again
3. Check backend logs for sync errors

### Wipe operation failed

**Check**:
- Device agent logs for error details
- Wipe operation status in dashboard
- Error message in the status display

**Common issues**:
- Folder path changed or deleted
- Permission errors (folder may be in use)
- Disk space issues

## Best Practices

1. **Approve Only Sensitive Folders**: Only approve folders containing sensitive data you'd want to wipe if device is stolen
2. **Regular Backups**: Ensure important data is backed up before approving folders for wipe
3. **Test First**: Test the wipe feature on a test folder before using in production
4. **Monitor Progress**: Watch the progress indicator to ensure wipe completes successfully
5. **Review Logs**: Check activity logs after wipe operations to verify completion

## Limitations

- Only works on folders explicitly approved by user
- System folders are always protected
- Wipe operations cannot be cancelled once started
- Deleted files cannot be recovered (permanent deletion)

## Support

For issues or questions:
1. Check device agent logs: `device_agent/agent.log`
2. Check backend logs for API errors
3. Review activity logs in dashboard
4. Check wipe operation status for error messages

---

**Note**: This feature is designed for security and data protection. Use responsibly and ensure you understand the implications of permanently deleting files.

