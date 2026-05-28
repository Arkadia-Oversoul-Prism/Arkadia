package com.sonata.app.di

import android.content.Context
import com.sonata.app.data.local.SettingsDataStore
import com.sonata.app.tts.piper.PiperEngine
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    
    @Provides
    @Singleton
    fun provideSettingsDataStore(
        @ApplicationContext context: Context
    ): SettingsDataStore {
        return SettingsDataStore(context)
    }
    
    @Provides
    @Singleton
    fun providePiperEngine(
        @ApplicationContext context: Context
    ): PiperEngine {
        return PiperEngine(context)
    }
}