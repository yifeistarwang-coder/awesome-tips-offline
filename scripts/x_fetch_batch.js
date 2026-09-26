/* Fetch full TweetDetail conversations for a list of focal tweet IDs.
 * Runs in the page context (x.com), reusing the logged-in browser session.
 *
 * Placeholders __QID__ and __BEARER__ are substituted by scripts/fetch_x_threads.py.
 * Input:  window.__ids = ["<tweet id>", ...]
 * Output: window.__batch = JSON string keyed by focal id, each value:
 *   {focal_id, author, conversation_id, chain_ids, chain: [...], extras: [...], error?}
 * Each item in `chain`/`extras` is a simplified tweet (text, photos, videos, links,
 * quoted tweet, article, timestamps) with t.co links expanded and media links removed.
 */
(function () {
  var IDS = window.__ids || [];
  window.__batch = 'PENDING';
  var qid = '__QID__';
  var bearer = '__BEARER__';
  var features = {"rweb_video_screen_enabled":false,"payments_enabled":false,"rweb_xchat_enabled":false,"profile_label_improvements_pcf_label_in_post_enabled":true,"rweb_tipjar_consumption_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"premium_content_api_read_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"responsive_web_grok_analyze_button_fetch_trends_enabled":false,"responsive_web_grok_analyze_post_followups_enabled":true,"responsive_web_jetfuel_frame":true,"responsive_web_grok_share_attachment_enabled":true,"articles_preview_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"responsive_web_grok_show_grok_translated_post":false,"responsive_web_grok_analysis_button_from_backend":true,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_grok_image_annotation_enabled":true,"responsive_web_grok_community_note_auto_translation_is_enabled":false,"responsive_web_enhance_cards_enabled":false};

  function unwrap(t) {
    if (!t) return null;
    if (t.__typename === 'TweetWithVisibilityResults') return t.tweet || null;
    if (t.__typename === 'Tweet') return t;
    if (t.legacy) return t;
    return null;
  }
  function coreUser(t) {
    try { return t.core.user_results.result.core || {}; } catch (e) { return {}; }
  }
  function bigId(a, b) {
    try {
      var A = BigInt(a), B = BigInt(b);
      return A < B ? -1 : (A > B ? 1 : 0);
    } catch (e) { return a < b ? -1 : (a > b ? 1 : 0); }
  }

  function simplify(t) {
    var leg = t.legacy || {};
    var note = null;
    try { note = t.note_tweet.note_tweet_results.result; } catch (e) {}
    var text = (note && note.text) ? note.text : (leg.full_text || '');
    var entityUrls = (note && note.entity_set && note.entity_set.urls) || (leg.entities && leg.entities.urls) || [];
    var mediaList = (leg.extended_entities && leg.extended_entities.media) || (leg.entities && leg.entities.media) || [];
    if ((!mediaList || !mediaList.length) && note && note.media && note.media.media_entities) mediaList = note.media.media_entities;
    var mediaShort = {};
    var photos = [];
    var videos = [];
    mediaList.forEach(function (m) {
      mediaShort[m.url] = true;
      if (m.type === 'photo') {
        var u = m.media_url_https;
        photos.push({ url: u + (u.indexOf('?') < 0 ? '?' : '&') + 'name=orig', alt: m.ext_alt_text || '', media_id: m.id_str });
      } else if (m.type === 'video' || m.type === 'animated_gif') {
        var variants = (m.video_info && m.video_info.variants) || [];
        var mp4s = variants.filter(function (v) { return v.content_type === 'video/mp4'; });
        mp4s.sort(function (a, b) { return (b.bitrate || 0) - (a.bitrate || 0); });
        videos.push({
          type: m.type,
          poster: m.media_url_https,
          url: mp4s.length ? mp4s[0].url : '',
          duration_ms: (m.video_info && m.video_info.duration_millis) || 0,
          media_id: m.id_str
        });
      }
    });
    text = text.replace(/https:\/\/t\.co\/[A-Za-z0-9]+/g, function (u) {
      if (mediaShort[u]) return '';
      for (var i = 0; i < entityUrls.length; i++) {
        if (entityUrls[i].url === u) return entityUrls[i].expanded_url;
      }
      return u;
    });
    var links = [];
    var seenUrls = {};
    entityUrls.forEach(function (e) {
      var x = e.expanded_url || e.url;
      if (!x) return;
      if (/^https?:\/\/(www\.)?(twitter|x)\.com\//.test(x)) return;
      if (seenUrls[x]) return;
      seenUrls[x] = true;
      links.push(x);
    });
    var card = null;
    try {
      var bv = t.card.legacy.binding_values;
      var get = function (k) {
        for (var i = 0; i < bv.length; i++) {
          if (bv[i].key === k) return bv[i].value.string_value || bv[i].value.image_value || null;
        }
        return null;
      };
      var cu = get('card_url');
      if (cu) card = { url: cu, title: get('title') || '', description: get('description') || '' };
    } catch (e) {}
    if (card && !seenUrls[card.url]) { seenUrls[card.url] = true; links.push(card.url); }
    var quoted = null;
    try {
      var q = unwrap(t.quoted_status_result && t.quoted_status_result.result);
      if (q) {
        var qu = coreUser(q);
        var qleg = q.legacy || {};
        quoted = { id: q.rest_id || qleg.id_str, author: qu.screen_name || '', name: qu.name || '', text: qleg.full_text || '', created_at: qleg.created_at || '' };
      }
    } catch (e) {}
    var article = null;
    try {
      var ar = t.article.article_results.result;
      if (ar) article = { title: ar.title || '', text: ar.plain_text || '' };
    } catch (e) {}
    var u = coreUser(t);
    var id = t.rest_id || leg.id_str;
    return {
      id: id,
      author: u.screen_name || '',
      name: u.name || '',
      created_at: leg.created_at || '',
      url: 'https://x.com/' + (u.screen_name || 'i') + '/status/' + id,
      text: text,
      photos: photos,
      videos: videos,
      links: links,
      card: card,
      quoted: quoted,
      article: article,
      in_reply_to: leg.in_reply_to_status_id_str || null,
      conversation_id: leg.conversation_id_str || null
    };
  }

  function collectTweets(data) {
    var all = {};
    (function walk(o, depth) {
      if (!o || typeof o !== 'object' || depth > 40) return;
      if (Array.isArray(o)) { o.forEach(function (x) { walk(x, depth + 1); }); return; }
      if (o.__typename === 'Tweet' || o.__typename === 'TweetWithVisibilityResults') {
        var t = unwrap(o);
        if (t) {
          var id = t.rest_id || (t.legacy && t.legacy.id_str);
          if (id) all[id] = t;
        }
      }
      for (var k in o) {
        if (k === 'quoted_status_result') continue;
        walk(o[k], depth + 1);
      }
    })(data, 0);
    return all;
  }

  function buildEntries(json) {
    var standalone = [];
    var modules = [];
    var instructions = [];
    try { instructions = json.data.threaded_conversation_with_injections_v2.instructions || []; } catch (e) {}
    instructions.forEach(function (inst) {
      if (inst.type !== 'TimelineAddEntries') return;
      (inst.entries || []).forEach(function (entry) {
        var content = entry.content || {};
        if (content.entryType === 'TimelineTimelineItem') {
          var tc = content.itemContent || {};
          var t = unwrap(tc.tweet_results && tc.tweet_results.result);
          if (t) standalone.push({ id: t.rest_id || (t.legacy && t.legacy.id_str), tweet: t, display: tc.tweetDisplayType || '' });
        } else if (content.entryType === 'TimelineTimelineModule') {
          var items = [];
          (content.items || []).forEach(function (it) {
            var ic = (it.item || {}).itemContent || {};
            var res = ic.tweet_results && ic.tweet_results.result;
            var tt = unwrap(res);
            if (tt) {
              items.push({ id: tt.rest_id || (tt.legacy && tt.legacy.id_str), tweet: tt, display: ic.tweetDisplayType || '', tombstone: false });
            } else if (res && res.__typename === 'TweetTombstone') {
              var m = /tweet-(\d+)/.exec(it.entryId || '');
              if (m) items.push({ id: m[1], tweet: null, display: ic.tweetDisplayType || '', tombstone: true, text: ((res.tombstone || {}).text || {}).text || 'This Post is unavailable.' });
            }
          });
          modules.push({ entryId: entry.entryId, items: items });
        }
      });
    });
    return { standalone: standalone, modules: modules };
  }

  function extract(json, focalId) {
    var all = collectTweets(json.data);
    var focal = all[focalId];
    if (!focal) return { focal_id: focalId, error: 'focal tweet not found in response', tweets_in_response: Object.keys(all).length };
    var author = coreUser(focal).screen_name || '';
    var conv = (focal.legacy || {}).conversation_id_str || '';
    var byAuthor = {};
    Object.keys(all).forEach(function (id) {
      var t = all[id];
      if (coreUser(t).screen_name === author && ((t.legacy || {}).conversation_id_str || '') === conv) byAuthor[id] = t;
    });

    // Rebuild the author's chain from the timeline structure: standalone tweet
    // entries (root + ancestors) and SelfThread module items (descendants), in
    // snowflake-id order. Tombstone items (deleted posts) are kept as gaps so
    // the chain does not silently jump over them.
    var built = buildEntries(json);
    var chainMap = {};
    built.standalone.forEach(function (s) {
      if (s.tweet && coreUser(s.tweet).screen_name === author && ((s.tweet.legacy || {}).conversation_id_str || '') === conv) {
        chainMap[s.id] = { id: s.id, tweet: s.tweet };
      }
    });
    built.modules.forEach(function (mod) {
      var hasSelfThread = mod.items.some(function (it) { return it.display === 'SelfThread' && !it.tombstone; });
      mod.items.forEach(function (it) {
        if (it.tombstone) {
          if (hasSelfThread) chainMap[it.id] = { id: it.id, tombstone: true, text: it.text };
        } else if (it.display === 'SelfThread' && coreUser(it.tweet).screen_name === author) {
          chainMap[it.id] = { id: it.id, tweet: it.tweet };
        }
      });
    });
    if (!chainMap[focalId]) chainMap[focalId] = { id: focalId, tweet: focal };
    if (Object.keys(chainMap).length === 1) {
      // Fallback for responses without a SelfThread module: reconnect by
      // walking in_reply_to links between author tweets.
      var children = {};
      Object.keys(byAuthor).forEach(function (id) {
        var p = (byAuthor[id].legacy || {}).in_reply_to_status_id_str;
        if (p && byAuthor[p]) {
          if (!children[p]) children[p] = [];
          children[p].push(id);
        }
      });
      var startId = focalId;
      while (true) {
        var parent = (byAuthor[startId].legacy || {}).in_reply_to_status_id_str;
        if (parent && byAuthor[parent]) startId = parent; else break;
      }
      (function dfs(id) {
        if (!chainMap[id]) chainMap[id] = { id: id, tweet: byAuthor[id] };
        (children[id] || []).slice().sort(bigId).forEach(dfs);
      })(startId);
    }
    var chain = Object.keys(chainMap).sort(bigId).map(function (id) {
      var e = chainMap[id];
      if (e.tombstone) return { id: id, tombstone: true, text: e.text || '' };
      return simplify(e.tweet);
    });
    var extras = Object.keys(byAuthor)
      .filter(function (id) { return !chainMap[id]; })
      .sort(bigId)
      .map(function (id) { return simplify(byAuthor[id]); });
    return {
      focal_id: focalId,
      author: author,
      conversation_id: conv,
      chain_ids: chain.map(function (x) { return x.id; }),
      chain: chain,
      extras: extras,
      tweets_in_response: Object.keys(all).length
    };
  }

  function fetchOne(id) {
    var variables = {
      focalTweetId: id,
      with_rux_injections: false,
      includePromotedContent: true,
      withCommunity: true,
      withQuickPromoteEligibilityTweetFields: true,
      withBirdwatchNotes: true,
      withVoice: true,
      withV2Timeline: true
    };
    var ct0 = (/ct0=([^;]+)/.exec(document.cookie) || [])[1] || '';
    var url = '/i/api/graphql/' + qid + '/TweetDetail?variables=' + encodeURIComponent(JSON.stringify(variables)) + '&features=' + encodeURIComponent(JSON.stringify(features));
    return fetch(url, {
      headers: {
        'authorization': 'Bearer ' + bearer,
        'x-csrf-token': ct0,
        'x-twitter-auth-type': 'OAuth2Session',
        'x-twitter-active-user': 'yes',
        'x-twitter-client-language': 'en'
      }
    }).then(function (r) {
      return r.text().then(function (t) { return { status: r.status, body: t }; });
    }).then(function (x) {
      if (x.status !== 200) return { focal_id: id, error: 'HTTP ' + x.status, detail: x.body.slice(0, 300) };
      var j;
      try { j = JSON.parse(x.body); } catch (e) { return { focal_id: id, error: 'invalid JSON response' }; }
      if (j.errors && !j.data) return { focal_id: id, error: 'graphql error', detail: JSON.stringify(j.errors).slice(0, 300) };
      return extract(j, id);
    }).catch(function (e) {
      return { focal_id: id, error: 'fetch failed: ' + (e && e.message || e) };
    });
  }

  Promise.all(IDS.map(fetchOne)).then(function (rs) {
    var out = {};
    rs.forEach(function (r) { out[r.focal_id] = r; });
    window.__batch = JSON.stringify(out);
  }).catch(function (e) {
    window.__batch = 'ERROR: ' + (e && e.message || e);
  });
  return 'started:' + IDS.length;
})();
