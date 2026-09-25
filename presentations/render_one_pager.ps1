$ErrorActionPreference='Stop'
$app=New-Object -ComObject PowerPoint.Application
$deck=$null
try {
 $deck=$app.Presentations.Open('C:\Users\aksha\Downloads\Fan-Agent_Executive_OnePager.pptx',$true,$false,$false)
 $deck.Export('D:\AI assisted simulation\Foam-Agent-main\fan-agent\presentations\onepager-preview','PNG',1600,900)
 $deck.SaveAs('C:\Users\aksha\Downloads\Fan-Agent_Executive_OnePager.pdf',32)
 Write-Output 'One-page PowerPoint and PDF rendered.'
} finally { if ($deck) {$deck.Close()}; $app.Quit() }
