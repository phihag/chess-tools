<?php
$id = isset($_GET['id']) ? \intval($_GET['id']) : '';
if ($id) {
	$opts = [
	    'https' => [
	        'method' => 'GET',
	        'header' => 'User-Agent: chess-tools (phihag@phihag.de)\r\n',
	    ],
	];
	$context = \stream_context_create($opts);

	$url = 'https://www.chess.com/callback/user/games?userId=' . \urlencode($id);
	$games_json = \file_get_contents($url, false, $context);
	$games = \json_decode($games_json, true);
	$error = null;
	if ($games === false) {
		$error = 'Download failed.';
	} else {
		$username = null;
		foreach ($games as $g) {
			for ($i = 1;$i <= 2;$i++) {
				$u = $g['user' . $i];
				if ($u['id'] === $id) {
					$username = $u['username'];
					break;
				}
			}
			if ($username) break;
		}
		if (!$username) {
			$error = 'Could not find player. No games?';
		}
	}
}

?>
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Look up chess.com username by ID</title>
<style type="text/css">
html, body {font-family: sans-serif;}
body {text-align: center;}
h1 {font-size: 40px;}
input, button {
	padding: 15px 15px;
	font-size: 30px;
}
#result {font-size: 40px;}
#error {font-size: 30px; color: red;}
</style>
</head>
<body>

<h1>Look up chess.com user by ID</h1>
<form method="get">
<input pattern="^[0-9]+$" required="required" title="Must be a number" placeholder="numeric ID" name="id" value="" autofocus="autofocus">
<button type="submit" style="margin-left: 10px">Look up username</button>
</form>

<?php
if ($id) {
	if ($error) {
		echo '<p id="error">Error while fetching username of <code>' . \htmlspecialchars($id) . '</code>: ';
		echo \htmlspecialchars($error) . ' Contact R_Doofus.';
	} else {
		echo (
			'<p id="result"><code>' . \htmlspecialchars($id) . '</code> is user ' .
			'<a href="https://www.chess.com/member/' . \htmlspecialchars($username) . '">' .
			htmlspecialchars($username) . '</a></p>');
	}
}
?>
</body>
</html>