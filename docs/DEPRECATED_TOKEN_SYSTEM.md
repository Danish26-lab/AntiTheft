# Deprecated Token-Based System - Removal Guide

## Overview

The token-based device registration system has been replaced with Agent-First Architecture (Prey Project style). This document lists what can be safely removed.

## ❌ Remove These Endpoints

### `backend/routes/device_routes.py`

**Can Remove:**
- `POST /api/devices/agent/auto-register` (lines ~237-425)
  - Old token-based registration endpoint
  - Replaced by: `POST /api/agent/register`

- `GET /api/devices/pending-link` (lines ~427-465)
  - Token polling endpoint
  - No longer needed with agent-first architecture

### `backend/routes/user_routes.py`

**Can Remove:**
- Token generation in `register_user()` (lines ~124-133)
  - DeviceLinkToken creation
  - Token return in response

**Keep:**
- Device linking logic (using device_id/fingerprint_hash) ✅

## ❌ Remove These Agent Methods

### `device_agent/agent.py`

**Can Remove:**
- `_poll_for_pending_token()` method
- `_register_with_token_and_hardware()` method
- Any calls to token-based registration

**Keep:**
- `_attempt_auto_registration()` ✅ (uses fingerprint, not token)
- `_start_local_server()` ✅

## ❌ Remove These Frontend Features

### Already Removed ✅
- Token file download in `SignUp.jsx`

## ❌ Can Remove These Files (Optional)

- `device_agent/register_device.py` (if only used for tokens)
- `device_agent/register_hardware.py` (manual registration script)

## ✅ Keep These (May Be Used Elsewhere)

- `DeviceLinkToken` model (may be used by other features)
- Token-based endpoints (for backward compatibility during transition)

## Migration Notes

Existing devices registered via tokens will continue to work. The new agent-first system is the preferred method going forward.
