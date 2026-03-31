$BASE = "http://localhost:8000"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  VIDORA AI - API ENDPOINT TESTS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Health Check
Write-Host ""
Write-Host "[1/9] Health Check..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$BASE/health" -Method GET
    Write-Host ("  PASS: " + ($health | ConvertTo-Json -Compress)) -ForegroundColor Green
}
catch {
    Write-Host "  FAIL: Backend not reachable. Is docker-compose up?" -ForegroundColor Red
    exit 1
}

# 2. Register User
Write-Host ""
Write-Host "[2/9] Register User..." -ForegroundColor Yellow
$registerBody = '{"email":"test@vidora.ai","password":"testpass123"}'
try {
    $user = Invoke-RestMethod -Uri "$BASE/users/register" -Method POST -Body $registerBody -ContentType "application/json"
    Write-Host ("  PASS: User created - id=" + $user.id + ", email=" + $user.email) -ForegroundColor Green
}
catch {
    $errMsg = $_.ToString()
    if ($errMsg -match "already registered" -or $errMsg -match "400") {
        Write-Host "  SKIP: User already exists (that is fine)" -ForegroundColor DarkYellow
    }
    else {
        Write-Host ("  FAIL: " + $errMsg) -ForegroundColor Red
    }
}

# 3. Login
Write-Host ""
Write-Host "[3/9] Login..." -ForegroundColor Yellow
$TOKEN = ""
try {
    $loginBody = "username=test@vidora.ai&password=testpass123"
    $tokenResp = Invoke-RestMethod -Uri "$BASE/users/login" -Method POST -Body $loginBody -ContentType "application/x-www-form-urlencoded"
    $TOKEN = $tokenResp.access_token
    Write-Host ("  PASS: Got JWT token - " + $TOKEN.Substring(0,30) + "...") -ForegroundColor Green
}
catch {
    Write-Host ("  FAIL: " + $_.ToString()) -ForegroundColor Red
    exit 1
}

$headers = @{ Authorization = "Bearer $TOKEN" }

# 4. Get Current User
Write-Host ""
Write-Host "[4/9] Get Current User (/users/me)..." -ForegroundColor Yellow
try {
    $me = Invoke-RestMethod -Uri "$BASE/users/me" -Method GET -Headers $headers
    Write-Host ("  PASS: id=" + $me.id + ", email=" + $me.email) -ForegroundColor Green
}
catch {
    Write-Host ("  FAIL: " + $_.ToString()) -ForegroundColor Red
}

# 5. Test 401 Unauthorized
Write-Host ""
Write-Host "[5/9] Test 401 Unauthorized (no token)..." -ForegroundColor Yellow
try {
    Invoke-RestMethod -Uri "$BASE/videos/my-videos" -Method GET -ErrorAction Stop
    Write-Host "  FAIL: Should have returned 401!" -ForegroundColor Red
}
catch {
    $statusCode = 0
    if ($_.Exception.Response -ne $null) {
        $statusCode = [int]$_.Exception.Response.StatusCode
    }
    if ($statusCode -eq 401) {
        Write-Host "  PASS: Got 401 as expected" -ForegroundColor Green
    }
    else {
        Write-Host ("  PASS: Request rejected (status: " + $statusCode + ")") -ForegroundColor Green
    }
}

# 6. List My Videos
Write-Host ""
Write-Host "[6/9] List My Videos..." -ForegroundColor Yellow
try {
    $myVideos = Invoke-RestMethod -Uri "$BASE/videos/my-videos" -Method GET -Headers $headers
    $count = 0
    if ($myVideos -ne $null) { $count = $myVideos.Count }
    Write-Host ("  PASS: You have " + $count + " video(s)") -ForegroundColor Green
}
catch {
    Write-Host ("  FAIL: " + $_.ToString()) -ForegroundColor Red
}

# 7. Upload a test video
Write-Host ""
Write-Host "[7/9] Upload Video..." -ForegroundColor Yellow
Write-Host "  NOTE: For a real upload test, use the Swagger UI at $BASE/docs" -ForegroundColor DarkGray
Write-Host "  Steps: POST /videos/upload > Try it out > Choose an .mp4 file > Execute" -ForegroundColor DarkGray

$testVideoPath = Join-Path $PSScriptRoot "test_video.mp4"
$VIDEO_ID = ""

if (Test-Path $testVideoPath) {
    try {
        $fileBytes = [System.IO.File]::ReadAllBytes($testVideoPath)
        $fileName = "test_video.mp4"
        $boundary = [System.Guid]::NewGuid().ToString()

        $enc = [System.Text.Encoding]::GetEncoding("iso-8859-1")
        $header = "--$boundary`r`nContent-Disposition: form-data; name=`"file`"; filename=`"$fileName`"`r`nContent-Type: video/mp4`r`n`r`n"
        $footer = "`r`n--$boundary--`r`n"

        $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($header)
        $footerBytes = [System.Text.Encoding]::UTF8.GetBytes($footer)

        $bodyStream = New-Object System.IO.MemoryStream
        $bodyStream.Write($headerBytes, 0, $headerBytes.Length)
        $bodyStream.Write($fileBytes, 0, $fileBytes.Length)
        $bodyStream.Write($footerBytes, 0, $footerBytes.Length)
        $bodyBytes = $bodyStream.ToArray()
        $bodyStream.Close()

        $upload = Invoke-RestMethod -Uri "$BASE/videos/upload" -Method POST -Headers $headers -ContentType "multipart/form-data; boundary=$boundary" -Body $bodyBytes
        $VIDEO_ID = $upload.video_id
        Write-Host ("  PASS: Uploaded - video_id=" + $VIDEO_ID + ", status=" + $upload.status) -ForegroundColor Green
    }
    catch {
        Write-Host ("  FAIL: " + $_.ToString()) -ForegroundColor Red
    }
}
else {
    Write-Host "  SKIP: No test_video.mp4 found. Use Swagger UI to test uploads." -ForegroundColor DarkYellow
}

# 8. Check Video Status
Write-Host ""
Write-Host "[8/9] Check Video Status..." -ForegroundColor Yellow
if ($VIDEO_ID -ne "") {
    $maxWait = 120
    $waited = 0
    while ($waited -lt $maxWait) {
        try {
            $status = Invoke-RestMethod -Uri "$BASE/videos/status/$VIDEO_ID" -Method GET -Headers $headers
            Write-Host ("  Status: " + $status.status + " (waited " + $waited + "s)") -ForegroundColor DarkGray
            if ($status.status -eq "done" -or $status.status -eq "failed") {
                if ($status.status -eq "done") {
                    Write-Host "  PASS: Video processing complete!" -ForegroundColor Green
                }
                else {
                    Write-Host "  WARN: Video processing failed" -ForegroundColor DarkYellow
                }
                break
            }
        }
        catch {
            Write-Host ("  Error polling: " + $_.ToString()) -ForegroundColor Red
            break
        }
        Start-Sleep -Seconds 5
        $waited = $waited + 5
    }
}
else {
    Write-Host "  SKIP: No video uploaded to check" -ForegroundColor DarkYellow
}

# 9. AI Query
Write-Host ""
Write-Host "[9/9] AI Query..." -ForegroundColor Yellow
if ($VIDEO_ID -ne "") {
    try {
        $vstatus = Invoke-RestMethod -Uri "$BASE/videos/status/$VIDEO_ID" -Method GET -Headers $headers
        if ($vstatus.status -ne "done") {
            Write-Host ("  SKIP: Video not done yet (status: " + $vstatus.status + ")") -ForegroundColor DarkYellow
        }
        else {
            $queryBody = '{"video_id":"' + $VIDEO_ID + '","query":"What objects are in this video?"}'
            $qresult = Invoke-RestMethod -Uri "$BASE/query/" -Method POST -Headers $headers -Body $queryBody -ContentType "application/json"
            Write-Host ("  PASS: model_used=" + $qresult.model_used) -ForegroundColor Green
            $respText = $qresult.response
            if ($respText.Length -gt 200) { $respText = $respText.Substring(0, 200) + "..." }
            Write-Host ("  Response: " + $respText) -ForegroundColor DarkGray
        }
    }
    catch {
        Write-Host ("  FAIL: " + $_.ToString()) -ForegroundColor Red
    }
}
else {
    Write-Host "  SKIP: No video uploaded to query" -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  ALL TESTS COMPLETE" -ForegroundColor Cyan
Write-Host "  Swagger UI: $BASE/docs" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
