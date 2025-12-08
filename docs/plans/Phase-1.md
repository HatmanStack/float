# Phase 1: Backend HLS Generation

## Phase Goal

Implement server-side HLS streaming infrastructure. The Lambda function will generate meditation audio as HLS segments instead of a single file, upload segments progressively to S3 with pre-signed URLs, maintain a live playlist, and support MP3 download via server-side concatenation.

**Success Criteria**:
- FFmpeg outputs HLS segments (5-second duration)
- Segments upload to S3 as they're created
- Playlist updates after each segment
- Job status includes streaming metadata and pre-signed playlist URL
- MP3 download endpoint concatenates segments on demand
- Idempotent regeneration works (cached TTS, retry from FFmpeg)
- All unit tests pass with mocked S3/subprocess

**Estimated Tokens**: ~85,000

---

## Prerequisites

- Phase 0 read and understood
- Existing Float backend deploying successfully (`npm run deploy`)
- FFmpeg Lambda layer functional
- S3 buckets configured

---

## Tasks

### Task 1: Extend Job Model for HLS Metadata

**Goal**: Update the job data structure to track HLS streaming state, segment progress, and download availability.

**Files to Modify/Create**:
- `backend/src/services/job_service.py` - Add streaming/download fields to job model
- `backend/src/models/domain.py` - Add streaming-related data classes
- `backend/tests/unit/test_services.py` - Add tests for new job fields

**Prerequisites**:
- Understand current job structure (see Phase 0)

**Implementation Steps**:

1. Define new data structures for streaming metadata:
   - Create dataclasses for `StreamingInfo` (playlist_url, segments_completed, segments_total, started_at)
   - Create dataclass for `DownloadInfo` (available, url, downloaded)
   - These should be serializable to JSON for S3 storage

2. Extend `JobService` methods:
   - Modify `create_job` to initialize streaming/download fields when job_type is meditation
   - Add `update_streaming_progress` method to update segment count
   - Add `mark_streaming_complete` method to finalize streaming state
   - Add `mark_download_ready` method when MP3 is available
   - Add `mark_download_completed` method for cleanup tracking

3. Add new job status: `STREAMING` (between PROCESSING and COMPLETED)
   - Modify `JobStatus` enum in `backend/src/services/job_service.py` (lines 21-25)
   - Current enum: `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`
   - Add: `STREAMING = "streaming"` after PROCESSING
   - Job transitions: PENDING → PROCESSING → STREAMING → COMPLETED
   - STREAMING means segments are being generated, playback can begin

4. Ensure backward compatibility:
   - Jobs without streaming fields should work (non-HLS fallback)
   - Existing job polling logic should not break

**Verification Checklist**:
- [ ] New job created with streaming fields initialized to null/false
- [ ] `update_streaming_progress` correctly increments segment count
- [ ] Job status transitions work correctly
- [ ] Serialization to/from JSON works for all new fields
- [ ] Existing tests still pass

**Testing Instructions**:

Unit tests to write:
- Test job creation includes streaming metadata structure
- Test streaming progress updates
- Test status transitions (PENDING → PROCESSING → STREAMING → COMPLETED)
- Test backward compatibility with jobs missing streaming fields

Mocking required:
- Mock S3StorageService for all job persistence operations

Run tests:
```bash
cd backend && PYTHONPATH=. pytest tests/unit/test_services.py -v -k "job"
```

**Commit Message Template**:
```
Author & Commiter : HatmanStack
Email : 82614182+HatmanStack@users.noreply.github.com

feat(backend): extend job model for HLS streaming metadata

Add StreamingInfo and DownloadInfo dataclasses
Add STREAMING status to JobStatus enum
Add streaming progress update methods to JobService
```

---

### Task 2: Create HLS Segment Service

**Goal**: Create a new service that handles HLS-specific operations: generating pre-signed URLs, uploading segments, managing playlists.

**Files to Create**:
- `backend/src/services/hls_service.py` - New service for HLS operations
- `backend/tests/unit/test_hls_service.py` - Unit tests

**Files to Modify**:
- `backend/src/services/__init__.py` - Export new service

**Prerequisites**:
- Task 1 complete (job model extended)
- Understand S3StorageService patterns

**Implementation Steps**:

1. Create `HLSService` class with constructor taking `StorageService`:
   - Store reference to storage service
   - Define constants: SEGMENT_DURATION (5), URL_EXPIRY (3600)

2. Implement `get_hls_prefix` method:
   - Given user_id and job_id, return S3 key prefix: `{user_id}/hls/{job_id}/`

3. Implement `generate_playlist_url` method:
   - Generate pre-signed GET URL for playlist.m3u8
   - URL should expire in 1 hour

4. Implement `generate_segment_url` method:
   - Given segment index, generate pre-signed GET URL
   - Segment naming: `segment_{index:03d}.ts`

5. Implement `upload_segment` method:
   - Upload segment bytes to S3
   - Return success/failure

6. Implement `upload_playlist` method:
   - Upload/update playlist.m3u8 content
   - This is called after each segment upload

7. Implement `generate_live_playlist` method:
   - Generate HLS playlist content for live streaming
   - Include `#EXT-X-PLAYLIST-TYPE:EVENT` for growing playlist
   - Include `#EXTM3U`, `#EXT-X-VERSION:3`, `#EXT-X-TARGETDURATION:5`
   - Add `#EXTINF:5.0,` for each segment
   - Use pre-signed URLs for segment references
   - Do NOT include `#EXT-X-ENDLIST` until generation complete

8. Implement `finalize_playlist` method:
   - Add `#EXT-X-ENDLIST` to mark stream complete
   - Re-upload final playlist

9. Implement `get_tts_cache_key` method:
   - Return S3 key for cached TTS audio: `{user_id}/hls/{job_id}/voice.mp3`

10. Implement `upload_tts_cache` method:
    - Upload TTS audio for retry capability
    - Called after TTS generation, before FFmpeg

11. Implement `download_tts_cache` method:
    - Download cached TTS audio if exists
    - Used during retry attempts

12. Implement `cleanup_hls_artifacts` method:
    - Delete all segments, playlist, cached TTS for a job
    - Called after MP3 download or on TTL expiry

**Verification Checklist**:
- [ ] Pre-signed URLs are valid and accessible
- [ ] Playlist content is valid HLS format
- [ ] Segments upload successfully
- [ ] Playlist updates after each segment
- [ ] TTS cache upload/download works
- [ ] Cleanup removes all artifacts

**Testing Instructions**:

Unit tests to write:
- Test playlist generation produces valid HLS format
- Test segment URL generation with correct naming
- Test pre-signed URL expiration is set correctly
- Test playlist finalization adds ENDLIST
- Test cleanup calls delete for all expected keys

Mocking required:
- Mock boto3 S3 client for all operations
- Mock `generate_presigned_url` to return predictable URLs

Run tests:
```bash
cd backend && PYTHONPATH=. pytest tests/unit/test_hls_service.py -v
```

**Commit Message Template**:
```
Author & Commiter : HatmanStack
Email : 82614182+HatmanStack@users.noreply.github.com

feat(backend): add HLS service for segment and playlist management

Implement HLSService with segment upload, playlist generation
Add pre-signed URL generation for secure access
Add TTS caching for idempotent regeneration
```

---

### Task 3: Modify FFmpeg Service for HLS Output

**Goal**: Update FFmpegAudioService to output HLS segments instead of a single MP3 file, with progressive segment availability.

**Files to Modify/Create**:
- `backend/src/services/ffmpeg_audio_service.py` - Add HLS output method
- `backend/tests/unit/test_services.py` - Add FFmpeg HLS tests

**Prerequisites**:
- Task 2 complete (HLS service available)
- Understand current FFmpeg audio combination flow

**Implementation Steps**:

1. Add `HLSService` as optional constructor parameter:
   - For backward compatibility, make it optional
   - Store reference for segment upload callbacks

2. Create new method `combine_voice_and_music_hls`:
   - Similar signature to existing `combine_voice_and_music`
   - Additional parameters: `job_id`, `user_id`, callback for progress updates
   - Returns list of music used (same as current method)

3. Implement HLS FFmpeg command generation:
   - Replace single output file with HLS output
   - Key FFmpeg flags:
     - `-f hls` - HLS output format
     - `-hls_time 5` - 5-second segments
     - `-hls_segment_type mpegts` - TS segment format
     - `-hls_flags independent_segments` - Each segment independently decodable
     - `-hls_segment_filename '{output_dir}/segment_%03d.ts'` - Segment naming
     - Output: `{output_dir}/playlist.m3u8`

4. Implement progressive segment upload:
   - FFmpeg writes to local temp directory
   - Use filesystem watcher or polling to detect new segments
   - As each segment appears, upload to S3 via HLSService
   - Update playlist in S3 after each segment upload
   - Call progress callback with segment count

5. Handle the audio mixing pipeline for HLS:
   - Steps 1-4 (music selection, volume reduction, silence, voice prep) remain same
   - Step 5 changes: output HLS instead of single MP3
   - Use same filter_complex for mixing, just different output format

6. Implement cleanup of local temp files:
   - Delete local segments after upload
   - Delete local playlist after final upload

7. Add error handling:
   - If FFmpeg fails mid-generation, log which segments completed
   - If upload fails, retry with exponential backoff
   - Raise exception if unrecoverable

**Verification Checklist**:
- [ ] FFmpeg command includes correct HLS flags
- [ ] Segments are 5 seconds each (within tolerance)
- [ ] Segments upload progressively during generation
- [ ] Playlist updates after each segment
- [ ] Local temp files cleaned up
- [ ] Backward compatibility: old method still works

**Testing Instructions**:

Unit tests to write:
- Test FFmpeg command generation includes HLS flags
- Test segment detection and upload callback invocation
- Test error handling when FFmpeg fails
- Test local file cleanup after completion

Mocking required:
- Mock subprocess.run to simulate FFmpeg execution
- Mock HLSService for segment upload verification
- Mock filesystem operations for segment detection

Run tests:
```bash
cd backend && PYTHONPATH=. pytest tests/unit/test_services.py -v -k "ffmpeg"
```

**Commit Message Template**:
```
Author & Commiter : HatmanStack
Email : 82614182+HatmanStack@users.noreply.github.com

feat(backend): add HLS output mode to FFmpeg audio service

Add combine_voice_and_music_hls method for streaming output
Implement progressive segment upload during generation
Maintain backward compatibility with existing MP3 output
```

---

### Task 4: Create MP3 Concatenation Service

**Goal**: Implement server-side concatenation of HLS segments into a single MP3 file for download.

**Files to Create**:
- `backend/src/services/download_service.py` - New service for MP3 generation
- `backend/tests/unit/test_download_service.py` - Unit tests

**Files to Modify**:
- `backend/src/services/__init__.py` - Export new service

**Prerequisites**:
- Task 2 complete (HLS service for segment access)

**Implementation Steps**:

1. Create `DownloadService` class:
   - Constructor takes `StorageService`, `HLSService`
   - Store FFmpeg executable path from settings

2. Implement `generate_mp3` method:
   - Parameters: user_id, job_id
   - Returns: S3 key of generated MP3

3. Implementation flow:
   - List all segment files for the job from S3
   - Download segments to local temp directory
   - Create FFmpeg concat input file listing segments in order
   - Run FFmpeg to concatenate and convert to MP3
   - Upload resulting MP3 to S3 at `{user_id}/downloads/{job_id}.mp3`
   - Clean up local temp files
   - Return S3 key

4. FFmpeg concatenation command:
   - Use concat demuxer: `-f concat -safe 0 -i filelist.txt`
   - Convert to MP3: `-c:a libmp3lame -q:a 2`
   - Output to temp file, then upload

5. Implement `get_download_url` method:
   - Generate pre-signed GET URL for the MP3
   - 1-hour expiration

6. Implement `check_mp3_exists` method:
   - Check if MP3 already generated for job
   - Avoid regenerating if already exists

7. Error handling:
   - If any segment missing, raise clear error
   - If FFmpeg fails, log and raise
   - Clean up partial files on failure

**Verification Checklist**:
- [ ] All segments downloaded correctly
- [ ] FFmpeg concat produces valid MP3
- [ ] MP3 uploads to correct S3 location
- [ ] Pre-signed URL works for download
- [ ] Existing MP3 not regenerated
- [ ] Temp files cleaned up

**Testing Instructions**:

Unit tests to write:
- Test segment listing and ordering
- Test FFmpeg concat command generation
- Test MP3 upload to correct location
- Test pre-signed URL generation
- Test idempotency (skip if exists)

Mocking required:
- Mock S3 operations (list, download, upload)
- Mock subprocess for FFmpeg
- Mock filesystem operations

Run tests:
```bash
cd backend && PYTHONPATH=. pytest tests/unit/test_download_service.py -v
```

**Commit Message Template**:
```
Author & Commiter : HatmanStack
Email : 82614182+HatmanStack@users.noreply.github.com

feat(backend): add download service for MP3 concatenation

Implement segment concatenation via FFmpeg
Add pre-signed URL generation for downloads
Include idempotency check to avoid regeneration
```

---

### Task 5: Update Lambda Handler for HLS Flow

**Goal**: Modify the Lambda handler to use HLS generation for meditation requests and add download endpoint.

**Files to Modify/Create**:
- `backend/src/handlers/lambda_handler.py` - Update meditation flow, add download handler
- `backend/src/services/service_factory.py` - Wire up new services
- `backend/tests/unit/test_lambda_handler.py` - Update and add tests

**Prerequisites**:
- Tasks 1-4 complete (all services ready)

**Implementation Steps**:

1. Update `ServiceFactory` to create new services:
   - Add `create_hls_service` method
   - Add `create_download_service` method
   - Wire up dependencies correctly

2. Modify `process_meditation_async` method:
   - After TTS generation, cache audio via HLSService
   - Replace `combine_voice_and_music` call with `combine_voice_and_music_hls`
   - Pass progress callback that updates job streaming status
   - Update job status to STREAMING when first segment ready
   - Finalize playlist when generation complete
   - Update job status to COMPLETED with streaming info

3. Add retry logic for idempotent regeneration:
   - Check if TTS cache exists for job
   - If exists and generation_attempt > 1, skip TTS, use cached audio
   - Increment generation_attempt on retry
   - Maximum 3 attempts before failing job

4. Add download request handler:
   - New route: POST `/job/{job_id}/download`
   - Validate user owns the job
   - Check job status is COMPLETED
   - Call DownloadService to generate/get MP3
   - Return download URL
   - Mark download as completed in job (for cleanup)

5. Update job status response:
   - Include streaming metadata when status is STREAMING or COMPLETED
   - Include download availability
   - Generate fresh pre-signed playlist URL on each status request

6. Add cleanup trigger:
   - When download marked complete, trigger HLS artifact cleanup
   - Keep MP3 in downloads folder (has own TTL via lifecycle)

7. Backward compatibility:
   - Add feature flag check (environment variable `ENABLE_HLS_STREAMING`)
   - If disabled, use existing base64 flow
   - Job response indicates which mode was used

**Verification Checklist**:
- [ ] Meditation request triggers HLS generation
- [ ] Job status shows streaming progress
- [ ] Playlist URL is pre-signed and accessible
- [ ] Download endpoint generates MP3
- [ ] Download URL works
- [ ] Retry uses cached TTS
- [ ] Feature flag controls behavior
- [ ] Existing tests pass

**Testing Instructions**:

Unit tests to write:
- Test meditation flow triggers HLS service
- Test job status includes streaming metadata
- Test download endpoint validation
- Test retry logic uses cached TTS
- Test feature flag fallback to base64

Mocking required:
- Mock all services (HLS, Download, TTS, AI, Audio)
- Mock boto3 Lambda client for async invocation
- Mock S3 for job persistence

Run tests:
```bash
cd backend && PYTHONPATH=. pytest tests/unit/test_lambda_handler.py -v
```

**Commit Message Template**:
```
Author & Commiter : HatmanStack
Email : 82614182+HatmanStack@users.noreply.github.com

feat(backend): integrate HLS streaming into Lambda handler

Update meditation flow to use HLS generation
Add download endpoint for MP3 retrieval
Implement retry logic with TTS caching
Add feature flag for gradual rollout
```

---

### Task 6: Update SAM Template for New Endpoint

**Goal**: Add the download endpoint route to API Gateway configuration.

**Files to Modify/Create**:
- `backend/template.yaml` - Add download route

**Prerequisites**:
- Task 5 complete (handler ready for download requests)

**Implementation Steps**:

1. Add new API Gateway route:
   - Method: POST
   - Path: `/job/{job_id}/download`
   - Integration: Same Lambda function

2. Add environment variable for feature flag:
   - `ENABLE_HLS_STREAMING`: default to "true"

3. Verify CORS configuration includes new endpoint:
   - OPTIONS preflight should work for new route
   - Response headers should include proper CORS

4. No changes needed to:
   - Lambda permissions (S3 access already configured)
   - Lambda timeout (300s sufficient)
   - Lambda memory (1024MB sufficient)

**Verification Checklist**:
- [ ] New route appears in template
- [ ] Environment variable defined
- [ ] CORS works for new endpoint
- [ ] Template validates (`sam validate`)

**Testing Instructions**:

Validation:
```bash
cd backend && sam validate
```

No unit tests needed for template changes - validated by deployment.

**Commit Message Template**:
```
Author & Commiter : HatmanStack
Email : 82614182+HatmanStack@users.noreply.github.com

feat(backend): add download endpoint to SAM template

Add POST /job/{job_id}/download route
Add ENABLE_HLS_STREAMING environment variable
```

---

### Task 7: Add S3 Lifecycle Rules for Cleanup

**Goal**: Configure S3 lifecycle rules as a safety net for abandoned HLS artifacts.

**Files to Modify/Create**:
- `backend/template.yaml` - Add lifecycle configuration to S3 bucket (if bucket defined in template)
- OR document manual AWS Console configuration

**Prerequisites**:
- Task 6 complete

**Implementation Steps**:

1. Determine if S3 bucket is defined in SAM template:
   - If yes, add lifecycle configuration to template
   - If no (bucket created externally), document manual steps

2. Define lifecycle rules:
   - Rule 1: Delete objects under `*/hls/*/` prefix after 24 hours
   - Rule 2: Delete objects under `*/downloads/` prefix after 7 days
   - Rule 3: Existing job cleanup rules remain unchanged

3. If adding to template:
   - Use `AWS::S3::Bucket` LifecycleConfiguration property
   - Define rules with appropriate prefixes and expiration

4. If manual configuration:
   - Document steps in deployment guide
   - Include AWS CLI commands for automation

**Verification Checklist**:
- [ ] Lifecycle rules defined (template or documented)
- [ ] HLS artifacts expire after 24 hours
- [ ] Download MP3s expire after 7 days
- [ ] Existing data not affected

**Testing Instructions**:

This is infrastructure configuration - verify via AWS Console or CLI after deployment:
```bash
aws s3api get-bucket-lifecycle-configuration --bucket $BUCKET_NAME
```

**Commit Message Template**:
```
Author & Commiter : HatmanStack
Email : 82614182+HatmanStack@users.noreply.github.com

chore(backend): add S3 lifecycle rules for HLS cleanup

Configure 24-hour expiration for HLS artifacts
Configure 7-day expiration for download MP3s
```

---

### Task 8: Integration Test Suite for HLS Backend

**Goal**: Create comprehensive integration tests that verify the complete HLS flow with mocked AWS services.

**Files to Create**:
- `backend/tests/integration/test_hls_flow.py` - New integration test file
- `backend/tests/mocks/aws_mocks.py` - S3 mocking utilities (directory exists with `__init__.py` and `external_apis.py`)

**Prerequisites**:
- Tasks 1-7 complete

**Implementation Steps**:

1. Set up test fixtures:
   - Mock S3 client with in-memory storage
   - Mock FFmpeg subprocess to create fake segment files
   - Mock TTS service to return test audio bytes

2. Test: Complete HLS generation flow
   - Create job
   - Trigger meditation processing
   - Verify segments uploaded to mock S3
   - Verify playlist updates
   - Verify job status transitions
   - Verify final job state has streaming info

3. Test: Retry with cached TTS
   - Create job with existing TTS cache in mock S3
   - Set generation_attempt > 1
   - Trigger processing
   - Verify TTS service NOT called
   - Verify FFmpeg still runs
   - Verify segments generated

4. Test: Download MP3 generation
   - Set up job with segments in mock S3
   - Call download endpoint
   - Verify FFmpeg concat called
   - Verify MP3 uploaded
   - Verify download URL generated

5. Test: Cleanup after download
   - Mark download complete
   - Verify HLS artifacts deleted
   - Verify MP3 retained

6. Test: Error handling
   - Simulate FFmpeg failure
   - Verify job marked failed after max retries
   - Verify partial segments cleaned up

**Verification Checklist**:
- [ ] All integration tests pass
- [ ] Tests run without live AWS
- [ ] Tests complete in reasonable time (<30 seconds)
- [ ] Edge cases covered

**Testing Instructions**:

Run integration tests:
```bash
cd backend && PYTHONPATH=. pytest tests/integration/test_hls_flow.py -v
```

Ensure tests work in CI (no AWS credentials):
- All AWS calls must be mocked
- No network requests to AWS

**Commit Message Template**:
```
Author & Commiter : HatmanStack
Email : 82614182+HatmanStack@users.noreply.github.com

test(backend): add integration tests for HLS streaming flow

Test complete generation flow with mocked services
Test retry logic with cached TTS
Test MP3 download generation
Test cleanup after download
```

---

## Phase Verification

### Complete Test Suite
Run all backend tests:
```bash
cd backend && PYTHONPATH=. pytest tests/ -v --tb=short
```

All tests must pass before proceeding to Phase 2.

### Manual Verification Steps
After deployment:
1. Create meditation request via API
2. Poll job status, verify streaming metadata appears
3. Access playlist URL, verify valid HLS format
4. After completion, call download endpoint
5. Verify MP3 download URL works
6. Verify HLS artifacts cleaned up after download

### Integration Points Ready for Phase 2
- Job status endpoint returns streaming metadata and pre-signed playlist URL
- Playlist URL serves valid HLS content
- Download endpoint returns pre-signed MP3 URL
- Feature flag allows fallback to base64 mode

### Known Limitations
- No CloudFront caching (pre-signed S3 URLs only)
- Segments not individually resumable (full FFmpeg restart on retry)
- No partial MP3 download (must wait for full generation)

### Technical Debt
- Consider adding CloudFront in future for better performance
- Consider segment-level checkpointing for very long meditations
- Consider WebSocket for real-time progress updates
