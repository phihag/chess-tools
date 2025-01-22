<?php

$PAGE_SIZE = 50;
$CACHE_DIR = __DIR__ . \DIRECTORY_SEPARATOR . 'cache' . \DIRECTORY_SEPARATOR;
if (!\is_dir($CACHE_DIR)) {
	\mkdir($CACHE_DIR);
}

$PERSONALITIES = [
	'Inventor', 'Machine', 'Professor', 'Magician', 'Artist',
	'Grappler', 'Mad Scientist', 'Assassin', 'Wildcard', 'Anaconda', 'Technician',
	'Jester', 'Caveman', 'Mastermind', 'Swindler', 'Romantic'
];
$LOWER_PERSONALITIES = array_map('strtolower', $PERSONALITIES);

$opts = [
    'https' => [
        'method' => 'GET',
        'header' => 'User-Agent: chess-tools (phihag@phihag.de)\r\n',
    ],
];
$GLOBALS['stream_context'] = \stream_context_create($opts);
function download_url($url) {
	if (strpos($url, 'https://') !== 0) {
		die('Invalid URL, aborting');
	}
	$response_text = \file_get_contents($url, false, $GLOBALS['stream_context']);
	if (! $response_text) {
		throw new Error('Failed to download ' . $url);
	}

	return $response_text;
}

function clear_cache($topic_id) {
	if (!is_numeric($topic_id)) throw new Error('Invalid topic ID');

	$cached_files = glob($CACHE_DIR . $topic_id . '-page*.json');
	foreach ($cached_files as $cf) {
		unlink($cf);
	}
}

function download_topic($topic_id) {
	$PAGE_SIZE = $GLOBALS['PAGE_SIZE'];
	if (!is_numeric($topic_id)) throw new Error('Invalid topic ID');

	$res = [];
	for ($page=0;$page < 10000;$page++) {
		$cache_filename = $GLOBALS['CACHE_DIR'] . $topic_id . '-page' . $page . '.json';
		if (is_file($cache_filename)) {
			$response_data = json_decode(file_get_contents($cache_filename), true);
		} else {
			$url = (
				'https://api.chess.com/v1/forums/comments' .
				'?forumTopicId=' . urlencode($topic_id) .
				'&page=' . urlencode($page) .
				'&commentsPerPage=' . urlencode($PAGE_SIZE)
			);
			$response_json = download_url($url);
			$response_data = json_decode($response_json, true);
			if (count($response_data['data']['comments']) === $PAGE_SIZE) {
				file_put_contents($cache_filename, $response_json);
			}
		}
		if ($response_data['status'] !== 'success') {
			throw new Error('Response status of ' . $url . ' is ' . $response_data['status']);
		}

		$comments = $response_data['data']['comments'];
		if (count($comments) === 0) {
			break;
		}
		$res = array_merge($res, $comments);
	}
	return $res;
}

function handle_error($message) {
	\http_response_code(400);
	\header('Content-Type: text/plain');
	die($message);
}

$url = isset($_GET['url']) ? $_GET['url'] : false;
$reset_cache = isset($_GET['reset_cache']) ? $_GET['reset_cache'] === '1' : false;
$user_stats = isset($_GET['user_stats']) ? $_GET['user_stats'] === '1' : false;

$download = isset($_GET['download']) ? $_GET['download'] === '1' : false;
if ($url) {
	if (!\preg_match('#^https://(?:www\.)?chess\.com/forum/.*?/([-_a-z0-9]+)(?:\?|$)#', $url, $matches)) {
		handle_error('Invalid forum URL ' . $url);
	}
	$topic_name = $matches[1];

	// download forum and find the ID
	$forum_html = download_url($url);
	if (!\preg_match('/<div\s+class="forums-single-list">\s+<div\s+class="[^"]*" id="comment-([0-9]+)"/', $forum_html, $matches)) {
		handle_error('Cannot find forum ID in ' . $url);
	}
	$topic_id = $matches[1];

	if ($reset_cache) {
		clear_cache($topic_id);
	}

	$posts = download_topic($topic_id);

	$filename = ($user_stats ? 'forumusers_' : 'forum_') . $topic_name . '.csv';
	if ($download) {
		header('Content-Type: text/csv');
		header('Content-Disposition: attachment; filename="' . $filename . '"');
	} else {
		header('Content-Type: text/plain');
	}

	if ($user_stats) {
		$counts = [];
		foreach ($posts as $p) {
			$username = $p['username'];
			if (!\array_key_exists($username, $counts)) {
				$counts[$username] = 0;
			}
			$counts[$username] += 1;
		}
		arsort($counts);

		$out = fopen('php://output', 'w');
		fputcsv($out, ['user', 'message_count']);
		foreach ($counts as $username => $usercount) {
			fputcsv($out, [$username, $usercount]);
		}
	} else {
		$out = fopen('php://output', 'w');
		fputcsv($out, [
			'comment_id', 'comment_number', 'create_time',
			'user_id', 'username', 'country_id', 'premium_status',
			'chess_title', 'flair_code',
			'personality', 'body',
		]);
		foreach ($posts as $p) {
			$first_personality = '';
			$first_personality_pos = INF;
			$body_without_quotes = preg_replace('#<div class="fquote".*</div>#x', '', $p['body']);
			$lower_body = strtolower($body_without_quotes);
			for ($i = 0;$i < count($PERSONALITIES);$i++) {
				$pos = strpos($lower_body, $LOWER_PERSONALITIES[$i]);
				if ($pos !== false) {
					if ($pos < $first_personality_pos) {
						$first_personality_pos = $pos;
						$first_personality = $PERSONALITIES[$i];
					}
				}
			}
			$time = date('c', $p['create_date']);

			fputcsv($out, [
				$p['comment_id'], $p['comment_number'], $time,
				$p['user_id'], $p['username'], $p['country_id'], $p['premium_status'],
				$p['chess_title'] ? $p['chess_title'] : '', $p['flair_code'],
				$first_personality, $p['body'],
			]);
		}
	}

	exit();
}

?><!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="google" content="notranslate">
<meta http-equiv="Content-Language" content="en">

<title>chess.com forum to CSV</title>
<style>
html, body {
	font-size: 22px;
	font-family: sans-serif;
}

input {
	font-size: 22px;
}

form, p {
	text-align: center;
}
form {
	margin-top: 1em;
}
label {
	margin-top: 10px;
	display: block;
	font-size: 80%;
}
.button-container button {
	font-size: 30px;
	margin: 10px 0;
}
</style>
</head>
<body>

<form method="get">
	<input type="text" name="url" placeholder="https://www.chess.com/forum/…" size="60"/>
	<label><input type="checkbox" name="reset_cache" value="1">Reset cache</label>
	<label><input type="checkbox" name="user_stats" value="1">User stats instead of posts</label>
	<label><input type="checkbox" name="download" value="1">Download</label>
	<div class="button-container">
		<button type="submit">Export to CSV</button>
	</div>
</form>

<p>Questions? Bug reports? Contact <a href="mailto:phihag@phihag.de">phihag@phihag.de</a></p>

</body>
</html>