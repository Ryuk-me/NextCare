<script context="module">
	export const prerender = true
</script>

<script>
	import { notificationToast } from '$lib/NotificationToast'
	import lock_svg from '$lib/assets/reset/lock.svg'
	import { ENV, status_code } from '$lib/utils'
	// import Locked from 'carbon-icons-svelte/lib/Locked.svelte'

	let email = ''

	let is_loading = false
	async function sendResetPassword() {
		is_loading = true
		const resp = await fetch(ENV.VITE_FINDCARE_API_BASE_URL + '/api/v1/email/reset-password', {
			method: 'post',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				email
			})
		})
		const data = await resp.json()
		is_loading = false
		if (resp.status === status_code.HTTP_202_ACCEPTED) {
			notificationToast(data?.detail, false, 3000, 'success')
			return
		}
		notificationToast(data?.detail, false, 3000, 'error')
	}
</script>

<svelte:head>
	<title>Findcare Password Recovery</title>
</svelte:head>

<div class="w-screen h-screen flex flex-col justify-center items-center font-maven">
	<div
		class="flex flex-col justify-center items-center w-96 lg:w-[30rem] bg-white rounded drop-shadow-xl mb-8 px-8 py-7"
	>
		<div id="header" class="flex flex-col justify-center items-center">
			<div>
				<img src={lock_svg} alt="lock svg" class="w-32" />
				<!-- <Locked fill="#635bff" class="w-32 h-32" /> -->
			</div>
			<div>
				<h2 class="text-2xl font-semibold mt-6">Trouble Logging In?</h2>
			</div>
		</div>
		<hr class="h-2" />
		<div id="body" class="flex flex-col justify-center items-center">
			<div class="flex flex-col justify-center items-center mt-2">
				<p class="font-light text-base">
					Enter your email address associated with your account and we'll send you instruction to
					get back into your account.
				</p>
			</div>
			<form class="w-full mt-3 mb-2" on:submit|preventDefault={sendResetPassword}>
				<label for="email" class="font-bold">Email</label>
				<input
					bind:value={email}
					type="email"
					id="email"
					placeholder="your@domain.com"
					required
					class="block border rounded py-2 px-3 w-full mt-3 focus:outline-none focus:shadow-outline focus:ring-1 focus:ring-primary"
				/>
				{#if is_loading}
					<button
						disabled
						class="bg-[#7069f5] cursor-not-allowed text-white mb-3 font-medium py-2 mt-5 w-full rounded focus:outline-none focus:shadow-outline"
						><i class="loading fa fa-spinner fa-spin relative right-2" />Reset Password</button
					>
				{:else}
					<button
						class="bg-primary hover:bg-[#524af4] text-white mb-3 font-medium py-2 mt-5 w-full rounded focus:outline-none focus:shadow-outline"
						>Reset Password</button
					>
				{/if}
			</form>
			<div>
				<p>
					Return to <a href="/login" class="text-primary hover:font-semibold font-medium">Login</a>
				</p>
			</div>
		</div>
	</div>
	<p class="text-center">
		&copy;2022 <a href="./" class="text-primary font-semibold">FindCare</a>. All rights reserved.
	</p>
</div>
