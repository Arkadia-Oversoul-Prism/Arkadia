package com.sonata.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.CloudDownload
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Language
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Speed
import androidx.compose.material.icons.filled.VolumeUp
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.sonata.app.domain.model.Voice
import com.sonata.app.domain.model.VoiceGender
import com.sonata.app.ui.theme.Accent
import com.sonata.app.ui.theme.Background
import com.sonata.app.ui.theme.OnSurfaceVariant
import com.sonata.app.ui.theme.Primary
import com.sonata.app.ui.theme.Surface
import com.sonata.app.ui.theme.SurfaceElevated
import com.sonata.app.ui.theme.SurfaceVariant

@Composable
fun MainScreen(
    viewModel: MainViewModel = hiltViewModel()
) {
    var selectedTab by remember { mutableStateOf(0) }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Background)
            .padding(top = 48.dp)
    ) {
        // Header
        Text(
            text = "Sonata",
            style = MaterialTheme.typography.headlineMedium,
            color = Primary,
            fontWeight = FontWeight.Light,
            modifier = Modifier.padding(horizontal = 24.dp)
        )
        Text(
            text = "Your voice, everywhere",
            style = MaterialTheme.typography.bodyMedium,
            color = OnSurfaceVariant,
            modifier = Modifier.padding(horizontal = 24.dp, vertical = 8.dp)
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // Tab Row
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp),
            horizontalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            TabButton(
                text = "Voices",
                selected = selectedTab == 0,
                onClick = { selectedTab = 0 }
            )
            TabButton(
                text = "Playback",
                selected = selectedTab == 1,
                onClick = { selectedTab = 1 }
            )
            TabButton(
                text = "Settings",
                selected = selectedTab == 2,
                onClick = { selectedTab = 2 }
            )
        }
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // Content
        when (selectedTab) {
            0 -> VoicesTab(viewModel)
            1 -> PlaybackTab(viewModel)
            2 -> SettingsTab(viewModel)
        }
    }
}

@Composable
fun TabButton(
    text: String,
    selected: Boolean,
    onClick: () -> Unit
) {
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(8.dp))
            .background(if (selected) Accent else Color.Transparent)
            .clickable { onClick() }
            .padding(horizontal = 16.dp, vertical = 8.dp),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = text,
            style = MaterialTheme.typography.labelLarge,
            color = if (selected) Color.White else OnSurfaceVariant
        )
    }
}

@Composable
fun VoicesTab(viewModel: MainViewModel) {
    val voices by viewModel.availableVoices.collectAsState()
    val selectedVoice by viewModel.selectedVoice.collectAsState()
    val isDownloading by viewModel.isDownloading.collectAsState()
    
    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        items(voices) { voice ->
            VoiceCard(
                voice = voice,
                isSelected = selectedVoice?.id == voice.id,
                isDownloading = isDownloading && selectedVoice?.id == voice.id,
                onSelect = { viewModel.selectVoice(voice) },
                onDownload = { viewModel.downloadVoice(voice) },
                onDelete = { viewModel.deleteVoice(voice) }
            )
        }
        
        item {
            Spacer(modifier = Modifier.height(80.dp))
        }
    }
}

@Composable
fun VoiceCard(
    voice: Voice,
    isSelected: Boolean,
    isDownloading: Boolean,
    onSelect: () -> Unit,
    onDownload: () -> Unit,
    onDelete: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onSelect() },
        colors = CardDefaults.cardColors(
            containerColor = if (isSelected) SurfaceElevated else Surface
        ),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Gender icon
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .clip(CircleShape)
                    .background(if (voice.gender == VoiceGender.FEMALE) Accent else SurfaceElevated),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Default.VolumeUp,
                    contentDescription = null,
                    tint = Primary,
                    modifier = Modifier.size(24.dp)
                )
            }
            
            Spacer(modifier = Modifier.width(16.dp))
            
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = voice.name,
                    style = MaterialTheme.typography.titleMedium,
                    color = Primary
                )
                Text(
                    text = "${voice.language} • ${voice.gender.name.lowercase().replaceFirstChar { it.uppercase() }}",
                    style = MaterialTheme.typography.bodySmall,
                    color = OnSurfaceVariant
                )
                if (voice.isDownloaded) {
                    Text(
                        text = "Downloaded",
                        style = MaterialTheme.typography.labelSmall,
                        color = Color(0xFF10B981)
                    )
                }
            }
            
            when {
                isDownloading -> {
                    CircularProgressIndicator(
                        modifier = Modifier.size(24.dp),
                        color = Accent,
                        strokeWidth = 2.dp
                    )
                }
                voice.isDownloaded -> {
                    Row {
                        if (isSelected) {
                            Icon(
                                imageVector = Icons.Default.Check,
                                contentDescription = "Selected",
                                tint = Accent,
                                modifier = Modifier.size(24.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                        }
                        IconButton(onClick = onDelete) {
                            Icon(
                                imageVector = Icons.Default.Delete,
                                contentDescription = "Delete",
                                tint = OnSurfaceVariant
                            )
                        }
                    }
                }
                else -> {
                    IconButton(onClick = onDownload) {
                        Icon(
                            imageVector = Icons.Default.CloudDownload,
                            contentDescription = "Download",
                            tint = Accent
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun PlaybackTab(viewModel: MainViewModel) {
    val speed by viewModel.playbackSpeed.collectAsState()
    val pitch by viewModel.playbackPitch.collectAsState()
    val autoRead by viewModel.autoRead.collectAsState()
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 24.dp),
        verticalArrangement = Arrangement.spacedBy(24.dp)
    ) {
        // Speed slider
        SettingSlider(
            title = "Speed",
            value = speed,
            valueRange = 0.5f..2.0f,
            onValueChange = { viewModel.updateSpeed(it) },
            icon = Icons.Default.Speed,
            valueLabel = "${String.format("%.1f", speed)}x"
        )
        
        // Pitch slider
        SettingSlider(
            title = "Pitch",
            value = pitch,
            valueRange = 0.5f..2.0f,
            onValueChange = { viewModel.updatePitch(it) },
            icon = Icons.Default.Language,
            valueLabel = "${String.format("%.1f", pitch)}x"
        )
        
        // Auto-read toggle
        SettingToggle(
            title = "Auto-read selected text",
            description = "Automatically speak when text is selected",
            checked = autoRead,
            onCheckedChange = { viewModel.updateAutoRead(it) }
        )
        
        // Test button
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .clickable { viewModel.testSpeech() },
            colors = CardDefaults.cardColors(containerColor = Surface),
            shape = RoundedCornerShape(12.dp)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    imageVector = Icons.Default.PlayArrow,
                    contentDescription = null,
                    tint = Accent,
                    modifier = Modifier.size(24.dp)
                )
                Spacer(modifier = Modifier.width(16.dp))
                Text(
                    text = "Test speech with current settings",
                    style = MaterialTheme.typography.bodyMedium,
                    color = Primary
                )
            }
        }
        
        Spacer(modifier = Modifier.height(80.dp))
    }
}

@Composable
fun SettingSlider(
    title: String,
    value: Float,
    valueRange: ClosedFloatingPointRange<Float>,
    onValueChange: (Float) -> Unit,
    icon: ImageVector,
    valueLabel: String
) {
    Column {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = OnSurfaceVariant,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = title,
                    style = MaterialTheme.typography.bodyMedium,
                    color = Primary
                )
            }
            Text(
                text = valueLabel,
                style = MaterialTheme.typography.labelMedium,
                color = Accent
            )
        }
        
        Slider(
            value = value,
            onValueChange = onValueChange,
            valueRange = valueRange,
            colors = SliderDefaults.colors(
                thumbColor = Accent,
                activeTrackColor = Accent,
                inactiveTrackColor = SurfaceVariant
            ),
            modifier = Modifier.fillMaxWidth()
        )
    }
}

@Composable
fun SettingToggle(
    title: String,
    description: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = title,
                style = MaterialTheme.typography.bodyMedium,
                color = Primary
            )
            Text(
                text = description,
                style = MaterialTheme.typography.bodySmall,
                color = OnSurfaceVariant
            )
        }
        Switch(
            checked = checked,
            onCheckedChange = onCheckedChange,
            colors = SwitchDefaults.colors(
                checkedThumbColor = Accent,
                checkedTrackColor = Accent.copy(alpha = 0.5f),
                uncheckedThumbColor = OnSurfaceVariant,
                uncheckedTrackColor = SurfaceVariant
            )
        )
    }
}

@Composable
fun SettingsTab(viewModel: MainViewModel) {
    val darkMode by viewModel.darkMode.collectAsState()
    val opacity by viewModel.overlayOpacity.collectAsState()
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 24.dp),
        verticalArrangement = Arrangement.spacedBy(24.dp)
    ) {
        // Overlay opacity
        SettingSlider(
            title = "Overlay opacity",
            value = opacity,
            valueRange = 0.5f..1.0f,
            onValueChange = { viewModel.updateOverlayOpacity(it) },
            icon = Icons.Default.Settings,
            valueLabel = "${(opacity * 100).toInt()}%"
        )
        
        // Dark mode toggle
        SettingToggle(
            title = "Dark mode",
            description = "Use dark theme throughout the app",
            checked = darkMode,
            onCheckedChange = { viewModel.updateDarkMode(it) }
        )
        
        // Clear cache button
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .clickable { viewModel.clearCache() },
            colors = CardDefaults.cardColors(containerColor = Surface),
            shape = RoundedCornerShape(12.dp)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    imageVector = Icons.Default.Delete,
                    contentDescription = null,
                    tint = Color(0xFFEF4444),
                    modifier = Modifier.size(24.dp)
                )
                Spacer(modifier = Modifier.width(16.dp))
                Column {
                    Text(
                        text = "Clear cache",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Primary
                    )
                    Text(
                        text = "Remove downloaded voice models",
                        style = MaterialTheme.typography.bodySmall,
                        color = OnSurfaceVariant
                    )
                }
            }
        }
        
        Spacer(modifier = Modifier.height(80.dp))
    }
}