$ErrorActionPreference='Stop'
$app=New-Object -ComObject PowerPoint.Application
$deck=$null
try {
 $deck=$app.Presentations.Open('C:\Users\aksha\Downloads\Fan-Agent_Project_Update_Editable.pptx', $true, $false, $false)
 $deck.Export('D:\AI assisted simulation\Foam-Agent-main\fan-agent\presentations\preview','PNG',1280,720)
 $deck.SaveAs('C:\Users\aksha\Downloads\Fan-Agent_Project_Update_Preview.pdf',32)
 Write-Output ('PowerPoint rendered '+$deck.Slides.Count+' slides.')
} finally {
 if ($deck) {$deck.Close()}
 $app.Quit()
}
